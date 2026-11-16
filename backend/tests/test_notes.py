"""Notes between a client and the professional team (phase 12)."""

import pytest
from rest_framework.throttling import ScopedRateThrottle

from apps.notes.models import MAX_LENGTH, Note
from apps.notes.services import add_note
from tests.factories import NutritionistFactory, TrainerFactory, active_client, onboarded_client

pytestmark = pytest.mark.django_db

MINE = "/api/v1/me/notes"
INBOX = "/api/v1/notes/inbox"


def thread_url(client) -> str:
    return f"/api/v1/users/{client.id}/notes"


class TestClient:
    def test_writes_to_the_team_and_reads_the_thread_newest_first(self, auth_api):
        client = active_client(first_name="Ana", last_name="Ruiz")
        api = auth_api(client)
        add_note(
            client, TrainerFactory(first_name="Pau", last_name="Vidal"), "¿Qué tal la rodilla?"
        )

        created = api.post(MINE, {"body": "  Mejor, gracias  "})

        assert created.status_code == 201
        assert created.json()["body"] == "Mejor, gracias"
        assert created.json()["from_client"] is True
        assert created.json()["author_name"] == "Ana Ruiz"
        thread = api.get(MINE).json()
        assert thread["count"] == 2
        assert [note["body"] for note in thread["results"]] == [
            "Mejor, gracias",
            "¿Qué tal la rodilla?",
        ]
        assert thread["results"][1]["author_role"] == "trainer"

    @pytest.mark.parametrize(
        ("body", "code"), [("   ", "blank"), ("x" * (MAX_LENGTH + 1), "max_length")]
    )
    def test_invalid_notes(self, auth_api, body, code):
        response = auth_api(active_client()).post(MINE, {"body": body})

        assert response.status_code == 400
        assert response.json()["field_codes"] == {"body": [code]}

    def test_unread_notes_of_the_team_until_read(self, auth_api):
        client = active_client()
        api = auth_api(client)
        add_note(client, TrainerFactory(), "Sube la carga en sentadilla")
        add_note(client, NutritionistFactory(), "Revisa la cena")
        add_note(client, client, "Entendido")

        assert api.get(f"{MINE}/unread").json() == {"unread": 2}
        assert api.post(f"{MINE}/read").json() == {"unread": 0}
        assert api.get(f"{MINE}/unread").json() == {"unread": 0}
        # The client's own note stays unread for the team.
        assert Note.objects.get(body="Entendido").read_at is None

    def test_only_the_own_thread(self, auth_api):
        client, other = active_client(), active_client()
        add_note(other, TrainerFactory(), "Solo para el otro cliente")

        assert auth_api(client).get(MINE).json()["count"] == 0
        assert auth_api(client).get(thread_url(other)).status_code == 403

    def test_a_client_waiting_for_a_plan_can_write(self, auth_api):
        assert (
            auth_api(onboarded_client()).post(MINE, {"body": "¿Cuándo empiezo?"}).status_code == 201
        )

    def test_writing_is_throttled(self, auth_api, monkeypatch):
        monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"notes": "2/min"})
        api = auth_api(active_client())

        assert [api.post(MINE, {"body": "Hola"}).status_code for _ in range(3)] == [201, 201, 429]
        assert api.get(MINE).status_code == 200  # reading is not limited


class TestStaff:
    def test_reply_in_the_client_thread(self, auth_api, trainer):
        client = active_client()

        response = auth_api(trainer).post(thread_url(client), {"body": "Buen trabajo esta semana"})

        assert response.status_code == 201
        assert response.json()["from_client"] is False
        assert response.json()["author_role"] == "trainer"
        assert auth_api(client).get(MINE).json()["results"][0]["body"] == "Buen trabajo esta semana"

    def test_inbox_of_unread_client_notes(self, auth_api, trainer, nutritionist):
        first, second, quiet = active_client(), active_client(), active_client()
        add_note(first, first, "Duda sobre el plan")
        add_note(second, second, "Me duele el hombro")
        add_note(second, second, "Sigue doliendo")
        add_note(quiet, trainer, "Una nota del equipo no cuenta")

        inbox = auth_api(trainer).get(INBOX).json()

        assert [(row["client"]["id"], row["unread"]) for row in inbox] == [
            (second.id, 2),
            (first.id, 1),
        ]
        assert inbox[0]["last_note"] == "Sigue doliendo"
        assert inbox[0]["client"]["full_name"] == second.get_full_name()

        # Read by one professional: read for the whole team.
        assert auth_api(trainer).post(f"{thread_url(second)}/read").status_code == 200
        assert [row["client"]["id"] for row in auth_api(nutritionist).get(INBOX).json()] == [
            first.id
        ]

    def test_deactivated_clients_leave_the_inbox(self, auth_api, trainer):
        client = active_client()
        add_note(client, client, "Me doy de baja")
        client.is_active = False
        client.save()

        assert auth_api(trainer).get(INBOX).json() == []
        assert auth_api(trainer).get(thread_url(client)).status_code == 404

    def test_only_client_threads(self, auth_api, admin_user, trainer):
        assert auth_api(admin_user).get(thread_url(trainer)).status_code == 404

    def test_the_thread_survives_a_deleted_professional(self, auth_api):
        client, trainer = active_client(), TrainerFactory(first_name="Pau", last_name="Vidal")
        add_note(client, trainer, "Te dejo los ejercicios")
        trainer.delete()

        note = auth_api(client).get(MINE).json()["results"][0]
        assert (note["author_name"], note["author_role"]) == ("Pau Vidal", "trainer")
