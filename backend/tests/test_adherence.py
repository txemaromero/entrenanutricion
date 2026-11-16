"""Adherence of clients to their plan, for the staff (phase 12)."""

from datetime import date, datetime, time
from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.progress import adherence
from apps.training.models import WorkoutSession
from tests.factories import WeightRecordFactory, active_client, onboarded_client

pytestmark = pytest.mark.django_db

ASSIGNED = "2026-03-02 09:00:00"  # Monday; 3 days a week → Monday, Wednesday and Friday
TODAY = date(2026, 3, 30)  # Monday: the window is 3–30 March
# The 11 training days of the window before today (today is not over yet).
TRAINING_DAYS = [4, 6, 9, 11, 13, 16, 18, 20, 23, 25, 27]
URL = "/api/v1/adherence"


def client_assigned_on(moment=ASSIGNED, **kwargs):
    with freeze_time(moment):
        return active_client(**kwargs)


def train(user, *days, month=3):
    plan = user.training_plans.get(is_current=True)
    for day in days:
        WorkoutSession.objects.create(
            user=user,
            user_plan=plan,
            workout_name="Full body",
            completed_at=timezone.make_aware(datetime.combine(date(2026, month, day), time(18))),
        )


def row_for(user, today=TODAY):
    return adherence.adherence_rows(adherence.clients_with_plan().filter(pk=user.pk), today)[0]


class TestCalculation:
    def test_scheduled_between(self):
        week = (date(2026, 3, 2), date(2026, 3, 8))
        assert adherence.scheduled_between((0, 2, 4), *week) == 3
        assert adherence.scheduled_between((0, 2, 4), date(2026, 3, 8), date(2026, 3, 2)) == 0

    def test_every_scheduled_session_done_is_on_track(self):
        client = client_assigned_on()
        train(client, *TRAINING_DAYS)

        row = row_for(client)

        assert (row["sessions"], row["scheduled"], row["adherence_percent"]) == (11, 11, 100)
        assert row["status"] == adherence.ON_TRACK
        assert row["last_session_date"] == date(2026, 3, 27)
        assert row["days_since_last_session"] == 3

    def test_today_counts_once_the_client_has_trained(self):
        client = client_assigned_on()
        train(client, *TRAINING_DAYS, 30)

        row = row_for(client)

        assert (row["sessions"], row["scheduled"]) == (12, 12)
        assert row["days_since_last_session"] == 0

    def test_two_workouts_on_the_same_day_count_as_one_day(self):
        client = client_assigned_on()
        train(client, *TRAINING_DAYS[:-1], 25)

        row = row_for(client)

        assert (row["sessions"], row["scheduled"], row["adherence_percent"]) == (10, 11, 91)

    def test_low_adherence_is_at_risk(self):
        client = client_assigned_on()
        train(client, 13, 18, 23, 25, 27)

        row = row_for(client)

        assert row["adherence_percent"] == 45  # 5 of 11
        assert row["status"] == adherence.AT_RISK

    def test_a_week_without_training_is_inactive(self):
        client = client_assigned_on()
        train(client, *TRAINING_DAYS[:8])  # last session on the 20th

        row = row_for(client)

        assert row["adherence_percent"] == 73
        assert row["days_since_last_session"] == 10
        assert row["status"] == adherence.INACTIVE

    def test_a_new_plan_has_nothing_scheduled_yet(self):
        new = client_assigned_on("2026-03-30 08:00:00")
        idle = client_assigned_on("2026-03-22 08:00:00")

        new_row, idle_row = row_for(new), row_for(idle)

        assert (new_row["scheduled"], new_row["adherence_percent"]) == (0, None)
        assert new_row["status"] == adherence.ON_TRACK
        assert new_row["last_session_date"] is None
        # Eight days after the assignment without a single session.
        assert idle_row["scheduled"] == 3
        assert idle_row["status"] == adherence.INACTIVE

    def test_weight_change_against_four_weeks_ago(self):
        client = client_assigned_on()
        WeightRecordFactory(user=client, weight_kg=Decimal("79.2"), date=date(2026, 3, 1))
        WeightRecordFactory(user=client, weight_kg=Decimal("78.0"), date=date(2026, 3, 28))

        row = row_for(client)

        assert row["current_weight_kg"] == 78.0
        assert row["weight_change_kg"] == -1.2

    def test_custom_training_days(self):
        client = client_assigned_on()
        client.details.training_days = [1, 3]  # Tuesday and Thursday
        client.details.weekly_training_days = 2
        client.details.save()
        train(client, 3, 5, 10, 12, 17, 19, 24, 26)

        row = row_for(client)

        assert (row["sessions"], row["scheduled"], row["adherence_percent"]) == (8, 8, 100)


@freeze_time("2026-03-30 12:00:00")
class TestEndpoints:
    @pytest.fixture
    def clients(self):
        on_track = client_assigned_on(last_name="Alonso")
        train(on_track, *TRAINING_DAYS)
        at_risk = client_assigned_on(last_name="Benítez")
        train(at_risk, 25, 27)
        inactive = client_assigned_on(last_name="Castro")
        train(inactive, 4, 6)
        onboarded_client()  # no plan: not listed
        gone = client_assigned_on(last_name="Domínguez")
        gone.is_active = False
        gone.save()
        return {"on_track": on_track, "at_risk": at_risk, "inactive": inactive}

    def test_worst_first_with_the_count_per_status(self, auth_api, trainer, clients):
        body = auth_api(trainer).get(URL).json()

        assert body["count"] == 3
        assert [row["user"]["id"] for row in body["results"]] == [
            clients["inactive"].id,
            clients["at_risk"].id,
            clients["on_track"].id,
        ]
        assert body["counts"] == [
            {"status": "inactive", "count": 1},
            {"status": "at_risk", "count": 1},
            {"status": "on_track", "count": 1},
        ]
        first = body["results"][0]
        assert first["user"]["full_name"] == clients["inactive"].get_full_name()
        assert first["plan_name"]
        assert first["status"] == "inactive"

    def test_distribution_and_average_of_the_whole_list(self, auth_api, trainer, clients):
        api = auth_api(trainer)
        body = api.get(URL).json()

        percents = [row["adherence_percent"] for row in body["results"]]
        expected = [0] * 5
        for percent in percents:
            if percent is not None:
                expected[min(percent // 20, 4)] += 1
        assert [(band["low"], band["high"]) for band in body["distribution"]] == [
            (0, 19),
            (20, 39),
            (40, 59),
            (60, 79),
            (80, 100),
        ]
        assert [band["count"] for band in body["distribution"]] == expected
        known = [percent for percent in percents if percent is not None]
        assert body["average_percent"] == round(sum(known) / len(known))
        # Like the counts, they describe every client, whatever the status filter.
        filtered = api.get(URL, {"status": "on_track"}).json()
        assert filtered["distribution"] == body["distribution"]
        assert filtered["average_percent"] == body["average_percent"]

    def test_nothing_scheduled_yet_is_left_out(self):
        from apps.progress.adherence import average_percent, distribution

        rows = [{"adherence_percent": None}, {"adherence_percent": 100}, {"adherence_percent": 19}]

        assert [band["count"] for band in distribution(rows)] == [1, 0, 0, 0, 1]
        assert average_percent(rows) == 60
        assert average_percent([{"adherence_percent": None}]) is None

    def test_filter_by_status_and_search(self, auth_api, nutritionist, clients):
        api = auth_api(nutritionist)

        at_risk = api.get(URL, {"status": "at_risk"}).json()
        assert [row["user"]["id"] for row in at_risk["results"]] == [clients["at_risk"].id]
        # The counts ignore the status filter.
        assert [entry["count"] for entry in at_risk["counts"]] == [1, 1, 1]

        found = api.get(URL, {"search": "alonso"}).json()
        assert [row["user"]["id"] for row in found["results"]] == [clients["on_track"].id]

        assert api.get(URL, {"status": "lazy"}).status_code == 400

    def test_query_budget(self, auth_api, trainer, clients, django_assert_max_num_queries):
        for _ in range(5):
            train(client_assigned_on(), 25, 27)
        api = auth_api(trainer)

        # Plus two for the access log of the clients of the page (their weight is health data).
        with django_assert_max_num_queries(10):
            assert api.get(URL).status_code == 200

    def test_one_client_with_the_last_four_weeks(self, auth_api, trainer, clients):
        body = auth_api(trainer).get(f"/api/v1/users/{clients['on_track'].id}/adherence").json()

        assert body["adherence_percent"] == 100
        assert [(week["start"], week["end"]) for week in body["weeks"]] == [
            ("2026-03-03", "2026-03-09"),
            ("2026-03-10", "2026-03-16"),
            ("2026-03-17", "2026-03-23"),
            ("2026-03-24", "2026-03-30"),
        ]
        assert [(week["sessions"], week["scheduled"]) for week in body["weeks"]] == [
            (3, 3),
            (3, 3),
            (3, 3),
            (2, 2),  # Monday the 30th is not over yet
        ]

    def test_client_without_plan_or_not_a_client(self, auth_api, admin_user, trainer):
        api = auth_api(admin_user)

        without_plan = api.get(f"/api/v1/users/{onboarded_client().id}/adherence")
        assert without_plan.status_code == 409
        assert without_plan.json()["code"] == "training_plan_not_assigned"
        assert api.get(f"/api/v1/users/{trainer.id}/adherence").status_code == 404

    def test_clients_cannot_see_it(self, auth_api, clients):
        api = auth_api(clients["on_track"])

        assert api.get(URL).status_code == 403
        assert api.get(f"/api/v1/users/{clients['at_risk'].id}/adherence").status_code == 403
