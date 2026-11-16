from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.accounts.models import User, UserStatus
from apps.core.demo_data import DEMO_PASSWORD
from apps.nutrition.models import Food, MealPlan
from apps.nutrition.services import calories_within_tolerance
from apps.training.models import (
    Exercise,
    ExerciseMedia,
    TrainingPlan,
    UserPlanWorkout,
    Workout,
    WorkoutSession,
)

pytestmark = pytest.mark.django_db


def counts():
    return {
        "users": User.objects.count(),
        "exercises": Exercise.objects.count(),
        "media": ExerciseMedia.objects.count(),
        "workouts": Workout.objects.count(),
        "plans": TrainingPlan.objects.count(),
        "meal_plans": MealPlan.objects.count(),
        "foods": Food.objects.count(),
        "sessions": WorkoutSession.objects.count(),
    }


SEED_PASSWORD = "Demo#Accounts-2026"


@pytest.fixture(autouse=True)
def demo_password(settings):
    """These tests seed with DEBUG off (--allow-production): it needs a password of its own."""
    settings.DEMO_PASSWORD = SEED_PASSWORD


@pytest.fixture
def seeded():
    call_command("seed_demo", "--allow-production", stdout=StringIO())
    return counts()


def test_refuses_to_run_without_debug():
    with pytest.raises(CommandError):
        call_command("seed_demo")


@pytest.mark.parametrize(
    ("password", "message"),
    [
        ("", "set DEMO_PASSWORD"),
        (DEMO_PASSWORD, "not the one published in the README"),
        ("12345678", "DEMO_PASSWORD is too weak"),
    ],
)
def test_outside_development_the_demo_needs_its_own_password(settings, password, message):
    settings.DEMO_PASSWORD = password

    with pytest.raises(CommandError, match=message):
        call_command("seed_demo", "--allow-production", stdout=StringIO())
    assert not User.objects.exists()


def test_development_uses_the_password_in_the_readme(settings, api_client):
    settings.DEBUG = True
    settings.DEMO_PASSWORD = ""

    call_command("seed_demo", stdout=StringIO())

    response = api_client.post(
        "/api/v1/auth/login",
        {"email": "cliente@entrenanutricion.dev", "password": DEMO_PASSWORD},
    )
    assert response.status_code == 200


def test_catalog_meets_the_minimums(seeded):
    assert seeded["exercises"] >= 20
    assert seeded["media"] >= 20
    assert seeded["workouts"] >= 6
    assert seeded["plans"] == 3
    assert seeded["meal_plans"] >= 6
    assert seeded["foods"] >= 30
    assert set(MealPlan.objects.values_list("category", flat=True)) == {
        "weight_loss",
        "muscle_gain",
        "maintenance",
    }
    assert all(
        calories_within_tolerance(p.calories, p.proteins_g, p.carbs_g, p.fats_g)
        for p in MealPlan.objects.all()
    )
    assert set(Workout.objects.values_list("name", flat=True)) >= {
        "Core",
        "Piernas",
        "Espalda y bíceps",
        "Pecho y tríceps",
        "Hombro",
        "Full body",
    }


def test_is_idempotent(seeded):
    call_command("seed_demo", "--allow-production", stdout=StringIO())

    assert counts() == seeded


def test_demo_users_and_states(seeded, api_client):
    statuses = dict(
        User.objects.filter(email__endswith="@entrenanutricion.dev").values_list("email", "status")
    )

    assert statuses["admin@entrenanutricion.dev"] == UserStatus.ACTIVE
    assert statuses["nuevo@entrenanutricion.dev"] == UserStatus.PENDING_ONBOARDING
    assert statuses["pendiente@entrenanutricion.dev"] == UserStatus.PENDING_ASSIGNMENT
    assert statuses["cliente@entrenanutricion.dev"] == UserStatus.ACTIVE
    for email in ("admin", "trainer", "nutri", "cliente"):
        response = api_client.post(
            "/api/v1/auth/login",
            {"email": f"{email}@entrenanutricion.dev", "password": SEED_PASSWORD},
        )
        assert response.status_code == 200


def test_active_client_history_is_consistent(seeded):
    client = User.objects.get(email="cliente@entrenanutricion.dev")
    assignment = client.training_plans.get(is_current=True)
    sessions = WorkoutSession.objects.filter(user=client).count()
    statuses = list(
        UserPlanWorkout.objects.filter(user_plan=assignment)
        .order_by("plan_workout__order")
        .values_list("status", flat=True)
    )

    assert sessions >= 20
    assert client.weight_records.count() >= 10
    assert statuses.count("available") == 1
    assert assignment.cycle == sessions // len(statuses) + 1


def test_growth_data_covers_two_years(seeded):
    years = set(
        User.objects.filter(email__endswith="@demo.entrenanutricion.dev").values_list(
            "date_joined__year", flat=True
        )
    )

    assert len(years) == 2


def test_demo_client_has_loads_and_records(seeded):
    from apps.training.services import personal_records

    client = User.objects.get(email="cliente@entrenanutricion.dev")
    records = {record["exercise"]["name"]: record for record in personal_records(client)}

    assert records, "the demo client should have personal records"
    squat = records.get("Sentadilla") or next(iter(records.values()))
    assert squat["best_weight_kg"] > 0
    assert squat["estimated_one_rm_kg"] >= squat["best_weight_kg"]


def test_demo_notes_with_the_team(seeded):
    from apps.notes.models import Note
    from apps.notes.services import staff_inbox, unread_for_client

    client = User.objects.get(email="cliente@entrenanutricion.dev")
    assert Note.objects.filter(client=client).count() == 4
    assert unread_for_client(client) == 1
    assert len(staff_inbox()) == 2

    call_command("seed_demo", "--allow-production", stdout=StringIO())
    assert Note.objects.count() == 6  # idempotent


def test_demo_menus_and_food_log(seeded):
    from apps.nutrition.menus import menu_of
    from apps.nutrition.models import FoodLogEntry

    for plan in MealPlan.objects.all():
        menu = menu_of(plan)
        assert menu["has_menu"], plan.name
        # Scaled to the plan's calories (grams are rounded to 5 g).
        assert menu["within_tolerance"], (plan.name, menu["calories_deviation_pct"])
    client = User.objects.get(email="cliente@entrenanutricion.dev")
    assert FoodLogEntry.objects.filter(user=client).dates("date", "day").count() == 6

    call_command("seed_demo", "--allow-production", stdout=StringIO())
    assert FoodLogEntry.objects.filter(user=client).dates("date", "day").count() == 6


def test_the_demo_catalog_is_in_three_languages(seeded):
    from apps.core import demo_data, demo_translations
    from apps.training.models import ExerciseStep

    groups = (
        (Exercise, [row[0] for row in demo_data.EXERCISES], demo_translations.EXERCISES),
        (Workout, [row[0] for row in demo_data.WORKOUTS], demo_translations.WORKOUTS),
        (
            TrainingPlan,
            [row[0] for row in demo_data.TRAINING_PLANS],
            demo_translations.TRAINING_PLANS,
        ),
        (MealPlan, [row[0] for row in demo_data.MEAL_PLANS], demo_translations.MEAL_PLANS),
    )
    for model, names, texts in groups:
        assert set(names) == set(texts), model.__name__  # nothing left untranslated
        for item in model.objects.filter(name__in=names):
            assert item.translations["en"]["name"] and item.translations["ca"]["name"], item.name
    assert {food[0] for food in demo_data.FOODS} == set(demo_translations.FOODS)
    assert Food.objects.filter(translations={}).count() == 0
    # Every step of every exercise has its translation.
    for exercise in Exercise.objects.filter(name__in=list(demo_translations.EXERCISES)):
        steps = ExerciseStep.objects.filter(exercise=exercise).count()
        assert len(exercise.translations["en"]["steps"]) == steps, exercise.name
        assert len(exercise.translations["ca"]["steps"]) == steps, exercise.name
