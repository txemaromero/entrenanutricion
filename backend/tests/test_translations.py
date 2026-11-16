"""Catalog content in the user's language (phase 14): Spanish base text, English and Catalan."""

from datetime import datetime, time
from decimal import Decimal

import pytest
from django.core import mail
from django.utils import timezone

from apps.nutrition.models import MealPlanItem
from apps.training.models import Exercise, ExerciseStep, WorkoutSession
from apps.training.reminders import send_due_reminders
from tests.factories import (
    ExerciseFactory,
    FoodFactory,
    MealPlanFactory,
    active_client,
    assign_meal_plan,
    assign_plan,
    onboarded_client,
    plan_with_workouts,
)

pytestmark = pytest.mark.django_db

EN = {"HTTP_ACCEPT_LANGUAGE": "en"}
CA = {"HTTP_ACCEPT_LANGUAGE": "ca"}


def squat():
    exercise = ExerciseFactory(
        name="Sentadilla",
        description="Flexión de rodillas con carga",
        translations={
            "en": {"name": "Squat", "description": "Knee bend with load", "steps": ["Stand up"]},
            "ca": {"name": "Esquat"},
        },
    )
    ExerciseStep.objects.create(exercise=exercise, order=1, text="Ponte de pie")
    ExerciseStep.objects.create(exercise=exercise, order=2, text="Baja despacio")
    return exercise


class TestLanguageOfTheResponses:
    def test_each_language_with_spanish_as_fallback(self, auth_api, trainer):
        exercise = squat()
        api = auth_api(trainer)
        url = f"/api/v1/exercises/{exercise.id}"

        spanish, english, catalan = (
            api.get(url).json(),
            api.get(url, **EN).json(),
            api.get(url, **CA).json(),
        )

        assert (spanish["name"], english["name"], catalan["name"]) == (
            "Sentadilla",
            "Squat",
            "Esquat",
        )
        assert english["description"] == "Knee bend with load"
        assert catalan["description"] == "Flexión de rodillas con carga"  # not translated
        # Steps: the second one has no English text yet.
        assert english["steps"] == ["Stand up", "Baja despacio"]

    def test_the_staff_get_every_language_to_edit(self, auth_api, trainer):
        exercise = squat()

        translations = (
            auth_api(trainer).get(f"/api/v1/exercises/{exercise.id}", **EN).json()["translations"]
        )

        assert translations["es"]["name"] == "Sentadilla"
        assert translations["es"]["steps"] == ["Ponte de pie", "Baja despacio"]
        assert translations["en"]["name"] == "Squat"
        assert translations["ca"] == {"name": "Esquat"}

    def test_lists_search_and_sort_in_the_language(self, auth_api, nutritionist):
        FoodFactory(name="Arroz", translations={"en": {"name": "Rice"}})
        FoodFactory(name="Zanahoria", translations={"en": {"name": "Carrot"}})
        FoodFactory(name="Brócoli")
        api = auth_api(nutritionist)

        names = [food["name"] for food in api.get("/api/v1/foods", **EN).json()["results"]]
        found = api.get("/api/v1/foods", {"search": "rice"}, **EN).json()["results"]

        assert names == ["Brócoli", "Carrot", "Rice"]
        assert [food["name"] for food in found] == ["Rice"]


class TestEditingTranslations:
    def test_the_trainer_saves_the_translations(self, auth_api, trainer):
        exercise = squat()

        response = auth_api(trainer).patch(
            f"/api/v1/exercises/{exercise.id}",
            {
                "translations": {
                    "es": {"name": "ignored: the Spanish text is the name field"},
                    "en": {"name": " Back squat ", "technique": "", "steps": ["Stand", "Go down"]},
                    "ca": {"name": "Esquat"},
                }
            },
            format="json",
        )

        assert response.status_code == 200
        exercise.refresh_from_db()
        assert exercise.name == "Sentadilla"
        assert exercise.translations == {
            "en": {"name": "Back squat", "steps": ["Stand", "Go down"]},
            "ca": {"name": "Esquat"},
        }

    @pytest.mark.parametrize(
        ("translations", "field", "code"),
        [
            ({"fr": {"name": "Squat"}}, "translations.fr", "invalid_language"),
            ({"en": {"colour": "red"}}, "translations.en.colour", "invalid_field"),
            ({"en": {"name": "x" * 121}}, "translations.en.name", "max_length"),
            ({"en": "Squat"}, "translations.en", "invalid"),
            ("Squat", "translations", "invalid"),
        ],
    )
    def test_invalid_translations(self, auth_api, trainer, translations, field, code):
        response = auth_api(trainer).patch(
            f"/api/v1/exercises/{squat().id}", {"translations": translations}, format="json"
        )

        assert response.status_code == 400
        assert code in response.json()["field_codes"][field]

    def test_empty_values_are_ignored(self, auth_api, nutritionist):
        food = FoodFactory(name="Arroz")

        response = auth_api(nutritionist).patch(
            f"/api/v1/foods/{food.id}",
            {"translations": {"en": {"name": "Rice", "steps": []}, "ca": {"name": None}}},
            format="json",
        )

        assert response.status_code == 200
        food.refresh_from_db()
        assert food.translations == {"en": {"name": "Rice"}}

    def test_meal_plans_and_foods_too(self, auth_api, nutritionist):
        plan = MealPlanFactory(name="Definición")
        api = auth_api(nutritionist)

        api.patch(
            f"/api/v1/meal-plans/{plan.id}",
            {"translations": {"en": {"name": "Cutting", "description": "Mild deficit"}}},
            format="json",
        )

        assert api.get(f"/api/v1/meal-plans/{plan.id}", **EN).json()["name"] == "Cutting"


class TestClientScreens:
    def test_the_plan_the_workout_and_the_exercise(self, auth_api):
        plan = plan_with_workouts(1)
        plan.translations = {"en": {"name": "Beginner plan"}}
        plan.save()
        workout = plan.plan_workouts.first().workout
        workout.translations = {"en": {"name": "Full body EN"}}
        workout.save()
        item = workout.items.first()
        item.exercise.translations = {"en": {"name": "Exercise EN"}}
        item.exercise.save()
        client = onboarded_client()
        assign_plan(client, plan)
        assign_meal_plan(client)
        api = auth_api(client)

        my_plan = api.get("/api/v1/me/training-plan", **EN).json()
        row = my_plan["workouts"][0]
        day = api.get(f"/api/v1/me/training-plan/workouts/{row['id']}", **EN).json()
        detail = api.get(f"/api/v1/me/exercises/{item.exercise_id}", **EN).json()
        dashboard = api.get("/api/v1/me/progress/dashboard", **EN).json()

        assert my_plan["plan"]["name"] == "Beginner plan"
        assert row["workout"]["name"] == "Full body EN"
        assert day["exercises"][0]["exercise"]["name"] == "Exercise EN"
        assert detail["name"] == "Exercise EN"
        assert dashboard["plan_name"] == "Beginner plan"
        assert dashboard["next_workout"]["workout_name"] == "Full body EN"

    def test_history_keeps_the_stored_name_and_translates_it(self, auth_api):
        client = active_client()
        plan = client.training_plans.get(is_current=True)
        workout = plan.plan.plan_workouts.first().workout
        workout.translations = {"en": {"name": "Legs"}}
        workout.save()
        WorkoutSession.objects.create(
            user=client, user_plan=plan, workout=workout, workout_name="Pierna (antes)"
        )
        api = auth_api(client)

        spanish = api.get("/api/v1/me/progress/history").json()["results"][0]["workout_name"]
        english = api.get("/api/v1/me/progress/history", **EN).json()["results"][0]["workout_name"]

        assert (spanish, english) == ("Pierna (antes)", "Legs")

    def test_nutrition_menu_shopping_list_and_diary(self, auth_api):
        client = active_client()
        plan = client.nutrition_plans.get(is_current=True).plan
        plan.translations = {"en": {"name": "Cutting"}}
        plan.save()
        rice = FoodFactory(name="Arroz", translations={"en": {"name": "Rice"}})
        MealPlanItem.objects.create(meal_plan=plan, meal="lunch", food=rice, grams=80)
        api = auth_api(client)

        assert api.get("/api/v1/me/nutrition-plan", **EN).json()["name"] == "Cutting"
        menu = api.get("/api/v1/me/nutrition-plan/menu", **EN).json()
        assert menu["meals"][1]["items"][0]["food"]["name"] == "Rice"
        shopping = api.get("/api/v1/me/shopping-list", **EN).json()
        assert shopping["items"][0]["food"]["name"] == "Rice"
        day = api.post(
            "/api/v1/me/food-log",
            {"date": str(timezone.localdate()), "meal": "lunch", "food_id": rice.id, "grams": 80},
            format="json",
            **EN,
        ).json()
        assert day["meals"][1]["entries"][0]["food_name"] == "Rice"
        assert (
            api.get("/api/v1/me/food-log").json()["meals"][1]["entries"][0]["food_name"] == "Arroz"
        )


class TestStaffScreensAndEmails:
    def test_user_list_and_conflicts_name_the_plans_in_the_language(
        self, auth_api, trainer, nutritionist
    ):
        client = active_client()
        assignment = client.training_plans.get(is_current=True)
        assignment.plan.translations = {"en": {"name": "Plan EN"}}
        assignment.plan.save()
        workout = assignment.plan.plan_workouts.first().workout

        users = auth_api(trainer).get("/api/v1/users", {"search": client.email}, **EN).json()
        conflict = auth_api(trainer).delete(f"/api/v1/workouts/{workout.id}", **EN).json()

        assert users["results"][0]["training_plan"]["name"] == "Plan EN"
        assert conflict["plans"][0]["name"] == "Plan EN"

    def test_the_reminder_uses_the_language_of_the_account(self):
        client = active_client()
        client.language = "en"
        client.save()
        client.details.reminders_enabled = True
        client.details.save()
        row = client.training_plans.get(is_current=True).workouts.get(status="available")
        workout = row.plan_workout.workout
        workout.translations = {"en": {"name": "Upper body"}}
        workout.save()
        monday = timezone.make_aware(datetime.combine(datetime(2026, 3, 2).date(), time(17, 10)))

        assert send_due_reminders(monday) == 1
        assert mail.outbox[0].subject == "Today is a training day: Upper body"

    def test_statistics_name_the_exercises_in_the_language(self, auth_api, admin_user):
        client = active_client()
        api = auth_api(client)
        row = client.training_plans.get(is_current=True).workouts.order_by("id").first()
        for item in row.plan_workout.workout.items.all():
            Exercise.objects.filter(pk=item.exercise_id).update(
                translations={"ca": {"name": f"Exercici {item.exercise_id}"}}
            )
            api.put(
                f"/api/v1/me/training-plan/workouts/{row.id}/exercises/{item.id}",
                {"completed": True},
                format="json",
            )
        api.post(f"/api/v1/me/training-plan/workouts/{row.id}/complete")
        year = timezone.localdate().year

        rows = (
            auth_api(admin_user)
            .get("/api/v1/statistics/exercise-popularity", {"year": year}, **CA)
            .json()["results"]
        )

        assert rows and all(row["name"].startswith("Exercici ") for row in rows)


def test_the_weight_of_decimal_values_is_not_affected():
    # Translations live in their own JSON field: the numbers of a food stay as they are.
    food = FoodFactory(calories=Decimal("123.4"), translations={"en": {"name": "Food"}})
    food.refresh_from_db()
    assert food.calories == Decimal("123.4")
