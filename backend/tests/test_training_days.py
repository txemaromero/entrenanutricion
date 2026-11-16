"""Custom training days (phase 9): they replace the default calendar."""

from datetime import date

import pytest
from freezegun import freeze_time

from apps.accounts.models import UserDetails
from apps.training.schedule import training_weekdays
from tests.factories import UserFactory, active_client, onboarded_client

DAYS = "/api/v1/me/training-days"
PLAN = "/api/v1/me/training-plan"
DASHBOARD = "/api/v1/me/progress/dashboard"
PROFILE = "/api/v1/me/profile"
MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

pytestmark = pytest.mark.django_db


def details_of(user) -> UserDetails:
    return UserDetails.objects.get(user=user)


class TestCalendar:
    def test_chosen_days_replace_the_default(self):
        assert training_weekdays(3, [SAT, TUE, THU]) == (TUE, THU, SAT)
        assert training_weekdays(3, []) == (MON, WED, FRI)
        assert training_weekdays(3, None) == (MON, WED, FRI)


class TestTrainingDaysApi:
    def test_default_calendar_until_the_client_picks_days(self, auth_api):
        body = auth_api(onboarded_client()).get(DAYS).json()

        assert body == {"days": [MON, WED, FRI], "custom": False, "weekly_training_days": 3}

    def test_pick_days(self, auth_api):
        client = onboarded_client()

        response = auth_api(client).put(DAYS, {"days": [THU, TUE, SAT]}, format="json")

        assert response.status_code == 200
        assert response.json() == {
            "days": [TUE, THU, SAT],
            "custom": True,
            "weekly_training_days": 3,
        }
        assert details_of(client).training_days == [TUE, THU, SAT]

    def test_the_number_of_days_becomes_the_weekly_training_days(self, auth_api):
        client = onboarded_client()

        body = auth_api(client).put(DAYS, {"days": [MON, TUE, THU, SUN]}, format="json").json()

        assert body["weekly_training_days"] == 4
        assert details_of(client).weekly_training_days == 4

    def test_empty_list_restores_the_default_calendar(self, auth_api):
        client = onboarded_client()
        api = auth_api(client)
        api.put(DAYS, {"days": [TUE, THU]}, format="json")

        body = api.put(DAYS, {"days": []}, format="json").json()

        assert body == {"days": [MON, THU], "custom": False, "weekly_training_days": 2}

    @pytest.mark.parametrize(
        ("days", "code"),
        [
            ([7], "max_value"),
            ([-1], "min_value"),
            ([MON, MON], "duplicated_choice"),
            ([MON, TUE, WED, THU, FRI, SAT, SUN], "max_length"),
            ("monday", "not_a_list"),
        ],
    )
    def test_invalid_days(self, auth_api, days, code):
        client = onboarded_client()

        response = auth_api(client).put(DAYS, {"days": days}, format="json")

        assert response.status_code == 400
        codes = {c for field_codes in response.json()["field_codes"].values() for c in field_codes}
        assert code in codes
        assert details_of(client).training_days == []

    def test_requires_the_onboarding_form(self, auth_api):
        response = auth_api(UserFactory()).get(DAYS)

        assert response.status_code == 409
        assert response.json()["code"] == "onboarding_not_completed"

    def test_only_for_clients(self, auth_api, trainer):
        assert auth_api(trainer).put(DAYS, {"days": [MON]}, format="json").status_code == 403


class TestConsistency:
    def test_changing_the_weekly_days_drops_the_chosen_days(self, auth_api):
        client = active_client()
        api = auth_api(client)
        api.put(DAYS, {"days": [TUE, THU, SAT]}, format="json")

        api.patch(PROFILE, {"weekly_training_days": 2}, format="json")

        details = details_of(client)
        assert details.weekly_training_days == 2
        assert details.training_days == []

    def test_keeping_the_weekly_days_keeps_the_chosen_days(self, auth_api):
        client = active_client()
        api = auth_api(client)
        api.put(DAYS, {"days": [TUE, THU, SAT]}, format="json")

        api.patch(PROFILE, {"weekly_training_days": 3, "goal": "maintain"}, format="json")

        assert details_of(client).training_days == [TUE, THU, SAT]

    def test_partial_saves_also_drop_stale_days(self):
        details = details_of(onboarded_client())
        details.training_days = [TUE, THU, SAT]
        details.save()

        details.weekly_training_days = 5
        details.save(update_fields=["weekly_training_days"])

        details.refresh_from_db()
        assert details.training_days == []

    def test_onboarding_form_cannot_set_the_days(self, auth_api):
        client = onboarded_client()
        api = auth_api(client)
        form = api.get("/api/v1/me/onboarding").json()

        api.put("/api/v1/me/onboarding", {**form, "training_days": [SUN]}, format="json")

        assert details_of(client).training_days == []

    def test_staff_see_the_chosen_days(self, auth_api, trainer):
        client = onboarded_client()
        auth_api(client).put(DAYS, {"days": [TUE, SAT]}, format="json")

        body = auth_api(trainer).get(f"/api/v1/users/{client.id}").json()

        assert body["onboarding"]["training_days"] == [TUE, SAT]


class TestScheduleUsesTheChosenDays:
    @freeze_time("2026-11-02 08:00:00")  # Monday
    def test_training_plan_dates(self, auth_api):
        client = active_client()
        api = auth_api(client)
        api.put(DAYS, {"days": [TUE, THU, SAT]}, format="json")

        body = api.get(PLAN).json()

        assert body["training_days"] == [TUE, THU, SAT]
        assert body["custom_training_days"] is True
        assert [row["scheduled_date"] for row in body["workouts"]] == [
            "2026-11-03",
            "2026-11-05",
            "2026-11-07",
        ][: len(body["workouts"])]

    @freeze_time("2026-11-02 08:00:00")
    def test_default_dates_are_reported_as_not_custom(self, auth_api):
        body = auth_api(active_client()).get(PLAN).json()

        assert body["training_days"] == [MON, WED, FRI]
        assert body["custom_training_days"] is False

    @freeze_time("2026-11-04 10:00:00")
    def test_progress_calendar(self, auth_api):
        client = active_client()
        assignment = client.training_plans.get(is_current=True)
        assignment.date_started = date(2026, 11, 1)
        assignment.save()
        api = auth_api(client)
        api.put(DAYS, {"days": [SAT, SUN]}, format="json")

        body = api.get(DASHBOARD).json()

        assert body["scheduled_days"][:3] == ["2026-11-01", "2026-11-07", "2026-11-08"]
        assert len(body["scheduled_days"]) == 9
        assert body["next_workout"]["scheduled_date"] == "2026-11-07"
