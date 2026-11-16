"""Training time and email reminders (phase 12)."""

from datetime import date, datetime, time
from io import StringIO

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts.emails import header_text
from apps.training.models import WorkoutSession
from apps.training.reminders import send_due_reminders
from tests.factories import DEFAULT_PASSWORD, TrainerFactory, active_client, onboarded_client

pytestmark = pytest.mark.django_db

URL = "/api/v1/me/reminders"
MONDAY = date(2026, 3, 2)  # 3 days a week by default: Monday, Wednesday and Friday


def at(day: date, hour: int, minute: int = 0) -> datetime:
    """A local (Europe/Madrid) moment."""
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


def with_reminders(training_time=None, **kwargs):
    client = active_client(**kwargs)
    client.details.reminders_enabled = True
    client.details.training_time = training_time
    client.details.save()
    return client


class TestSettings:
    def test_off_by_default_with_the_default_time(self, auth_api):
        body = auth_api(active_client()).get(URL).json()

        assert body == {
            "enabled": False,
            "training_time": "18:00",
            "custom_time": False,
            "default_training_time": "18:00",
        }

    def test_turn_on_with_an_own_time_in_the_current_language(self, auth_api):
        client = active_client()
        api = auth_api(client)

        body = api.put(
            URL, {"enabled": True, "training_time": "07:30"}, HTTP_ACCEPT_LANGUAGE="ca"
        ).json()

        assert (body["enabled"], body["training_time"], body["custom_time"]) == (
            True,
            "07:30",
            True,
        )
        client.refresh_from_db()
        assert client.language == "ca"
        assert api.put(URL, {"enabled": True, "training_time": None}).json()["custom_time"] is False

    def test_the_countdown_uses_the_training_time(self, auth_api):
        client = active_client()
        api = auth_api(client)
        api.put(URL, {"enabled": False, "training_time": "07:30"})

        target = api.get("/api/v1/me/progress/dashboard").json()["next_workout"]["target_datetime"]

        assert timezone.localtime(datetime.fromisoformat(target)).time() == time(7, 30)

    @pytest.mark.parametrize("value", ["25:00", "7.30", "mañana"])
    def test_invalid_time(self, auth_api, value):
        response = auth_api(active_client()).put(URL, {"enabled": True, "training_time": value})

        assert response.status_code == 400
        assert response.json()["field_codes"] == {"training_time": ["invalid"]}

    def test_needs_the_onboarding_and_a_client(self, auth_api, client_user, trainer):
        assert auth_api(client_user).get(URL).json()["code"] == "onboarding_not_completed"
        assert auth_api(trainer).get(URL).status_code == 403


class TestLanguage:
    def test_profile_and_login_keep_the_language(self, auth_api, api_client):
        client = active_client(email="lang@example.com")

        me = auth_api(client).patch("/api/v1/me/profile", {"language": "en"}).json()
        assert me["language"] == "en"

        api_client.post(
            "/api/v1/auth/login",
            {"email": "lang@example.com", "password": DEFAULT_PASSWORD},
            HTTP_ACCEPT_LANGUAGE="ca-ES,ca;q=0.9",
        )
        client.refresh_from_db()
        assert client.language == "ca"

    def test_unknown_language(self, auth_api):
        response = auth_api(active_client()).patch("/api/v1/me/profile", {"language": "fr"})

        assert response.json()["field_codes"] == {"language": ["invalid_choice"]}


class TestSending:
    def test_within_the_hour_before_the_training_time(self):
        client = with_reminders(first_name="Lucía")

        assert send_due_reminders(at(MONDAY, 16, 50)) == 0
        assert send_due_reminders(at(MONDAY, 17, 10)) == 1

        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == [client.email]
        workout = client.training_plans.get(is_current=True).workouts.get(status="available")
        assert message.subject == f"Hoy toca entrenar: {workout.plan_workout.workout.name}"
        assert "Hola, Lucía" in message.body
        assert "a las 18:00" in message.body
        assert "/app/training" in message.body
        # Once a day.
        assert send_due_reminders(at(MONDAY, 17, 40)) == 0
        client.details.refresh_from_db()
        assert client.details.last_reminder_on == MONDAY

    def test_the_subject_is_one_clean_line(self):
        client = with_reminders()
        row = client.training_plans.get(is_current=True).workouts.get(status="available")
        workout = row.plan_workout.workout
        # Typed by staff: a line break would make Django refuse the email, and a bidi override
        # (U+202E) would disguise the subject.
        workout.name = "Pierna\r\nBcc: todos@example.com \u202e" + "a" * 85
        workout.save()

        assert send_due_reminders(at(MONDAY, 17, 10)) == 1

        subject = mail.outbox[0].subject
        assert subject.startswith("Hoy toca entrenar: Pierna Bcc: todos@example.com a")
        assert "\n" not in subject and "\r" not in subject and "\u202e" not in subject
        assert subject.endswith("…")
        assert workout.name.split("\r")[0] in mail.outbox[0].body

    def test_own_time_and_language(self):
        client = with_reminders(training_time=time(7, 30))
        client.language = "en"
        client.save()

        assert send_due_reminders(at(MONDAY, 6, 40)) == 1
        assert mail.outbox[0].subject.startswith("Today is a training day:")
        assert "at 07:30" in mail.outbox[0].body

    def test_no_reminder_when_it_does_not_apply(self):
        off = active_client()
        trained = with_reminders()
        WorkoutSession.objects.create(
            user=trained, workout_name="Full body", completed_at=at(MONDAY, 9)
        )
        gone = with_reminders()
        gone.is_active = False
        gone.save()
        without_plan = onboarded_client()
        without_plan.details.reminders_enabled = True
        without_plan.details.save()
        TrainerFactory()

        assert send_due_reminders(at(MONDAY, 17, 10)) == 0
        assert mail.outbox == []
        assert off.details.reminders_enabled is False

    def test_not_on_rest_days(self):
        with_reminders()

        assert send_due_reminders(at(date(2026, 3, 3), 17, 10)) == 0  # Tuesday

    def test_custom_training_days(self):
        client = with_reminders()
        client.details.training_days = [1, 3]  # Tuesday and Thursday
        client.details.weekly_training_days = 2
        client.details.save()

        assert send_due_reminders(at(MONDAY, 17, 10)) == 0
        assert send_due_reminders(at(date(2026, 3, 3), 17, 10)) == 1

    def test_the_hourly_command(self):
        with_reminders()
        out = StringIO()

        with freeze_time(at(MONDAY, 17, 5)):
            call_command("send_training_reminders", "--dry-run", stdout=out)
            assert "1 training reminder(s) due." in out.getvalue()
            assert mail.outbox == []

            call_command("send_training_reminders", stdout=out)
            assert "1 training reminder(s) sent." in out.getvalue()
            assert len(mail.outbox) == 1

    def test_a_failing_mail_server_is_retried_next_hour(self, monkeypatch):
        client = with_reminders(training_time=time(19, 30))
        monkeypatch.setattr(
            "apps.accounts.emails.send_mail", lambda *args, **kwargs: (_ for _ in ()).throw(OSError)
        )

        assert send_due_reminders(at(MONDAY, 18, 40)) == 0
        client.details.refresh_from_db()
        assert client.details.last_reminder_on is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Pierna y glúteo", "Pierna y glúteo"),
        ("  Tren\tsuperior\n ", "Tren superior"),
        ("A\u200bB\u0000C", "ABC"),
        ("x" * 100, "x" * 79 + "…"),
    ],
)
def test_header_text(value, expected):
    assert header_text(value) == expected
