"""Sample day menus of the nutrition plans and the client's shopping list (phase 13)."""

from decimal import Decimal

import pytest

from apps.nutrition.models import Food, MealPlanItem
from tests.factories import FoodFactory, MealPlanFactory, active_client

pytestmark = pytest.mark.django_db


def menu_url(plan) -> str:
    return f"/api/v1/meal-plans/{plan.id}/menu"


def food(name, category="grains", calories=100, proteins=10, carbs=10, fats=2):
    return FoodFactory(
        name=name,
        category=category,
        calories=Decimal(calories),
        proteins_g=Decimal(proteins),
        carbs_g=Decimal(carbs),
        fats_g=Decimal(fats),
    )


@pytest.fixture
def foods():
    return {
        "oats": food("Avena", "grains", 380, 13, 60, 7),
        "chicken": food("Pollo", "meat", 110, 23, 0, 2),
        "rice": food("Arroz", "grains", 350, 7, 78, 1),
        "apple": food("Manzana", "fruits", 52, 0.3, 14, 0.2),
    }


def body(*rows):
    return {
        "items": [{"meal": meal, "food_id": item.id, "grams": grams} for meal, item, grams in rows]
    }


class TestMenuEditing:
    def test_the_nutritionist_composes_the_menu_and_sees_the_totals(
        self, auth_api, nutritionist, foods
    ):
        plan = MealPlanFactory(calories=1700)

        response = auth_api(nutritionist).put(
            menu_url(plan),
            body(
                ("breakfast", foods["oats"], 80),
                ("lunch", foods["chicken"], 200),
                ("lunch", foods["rice"], 100),
                ("snacks", foods["apple"], 150),
            ),
            format="json",
        )

        assert response.status_code == 200
        menu = response.json()
        assert menu["has_menu"] is True
        breakfast, lunch, dinner, snacks = menu["meals"]
        assert breakfast["items"][0]["food"] == {
            "id": foods["oats"].id,
            "name": "Avena",
            "category": "grains",
        }
        assert breakfast["totals"] == {
            "calories": 304.0,
            "proteins_g": 10.4,
            "carbs_g": 48.0,
            "fats_g": 5.6,
        }
        assert [item["food"]["name"] for item in lunch["items"]] == ["Pollo", "Arroz"]
        assert lunch["totals"]["calories"] == 570.0
        assert dinner["items"] == [] and dinner["totals"]["calories"] == 0
        # Targets of each meal follow the plan's distribution (lunch: 30 %).
        assert lunch["target"]["calories"] == 510.0
        assert menu["totals"]["calories"] == 304 + 570 + 78
        assert menu["target"]["calories"] == 1700
        assert menu["calories_deviation_pct"] == -44.0
        assert menu["within_tolerance"] is False

    def test_saving_replaces_the_whole_menu(self, auth_api, nutritionist, foods):
        plan = MealPlanFactory()
        api = auth_api(nutritionist)
        api.put(menu_url(plan), body(("lunch", foods["rice"], 100)), format="json")

        menu = api.put(
            menu_url(plan), body(("dinner", foods["chicken"], 150)), format="json"
        ).json()

        assert [len(meal["items"]) for meal in menu["meals"]] == [0, 0, 1, 0]
        assert MealPlanItem.objects.filter(meal_plan=plan).count() == 1
        assert api.put(menu_url(plan), {"items": []}, format="json").json()["has_menu"] is False

    def test_within_the_tolerance(self, auth_api, admin_user, foods):
        plan = MealPlanFactory(calories=1000)

        menu = (
            auth_api(admin_user)
            .put(menu_url(plan), body(("lunch", foods["rice"], 300)), format="json")
            .json()
        )

        assert (menu["calories_deviation_pct"], menu["within_tolerance"]) == (5.0, True)

    @pytest.mark.parametrize(
        ("row", "field", "code"),
        [
            ({"meal": "brunch", "grams": 10}, "items.0.meal", "invalid_choice"),
            ({"meal": "lunch", "grams": 0}, "items.0.grams", "min_value"),
            ({"meal": "lunch", "grams": 2001}, "items.0.grams", "max_value"),
            (
                {"meal": "lunch", "grams": 10, "food_id": 999999},
                "items.0.food_id",
                "does_not_exist",
            ),
        ],
    )
    def test_invalid_rows(self, auth_api, nutritionist, foods, row, field, code):
        payload = {"items": [{"food_id": foods["rice"].id, **row}]}

        response = auth_api(nutritionist).put(menu_url(MealPlanFactory()), payload, format="json")

        assert response.status_code == 400
        assert code in response.json()["field_codes"][field]

    def test_too_many_rows(self, auth_api, nutritionist, foods):
        rows = [("lunch", foods["rice"], 10)] * 61

        response = auth_api(nutritionist).put(
            menu_url(MealPlanFactory()), body(*rows), format="json"
        )

        assert response.json()["field_codes"]["items"] == ["max_length"]

    def test_trainers_read_and_clients_do_not(self, auth_api, trainer, foods):
        plan = MealPlanFactory()

        assert auth_api(trainer).get(menu_url(plan)).status_code == 200
        assert (
            auth_api(trainer).put(menu_url(plan), {"items": []}, format="json").status_code == 403
        )
        assert auth_api(active_client()).get(menu_url(plan)).status_code == 403

    def test_query_budget(self, auth_api, trainer, foods, django_assert_max_num_queries):
        plan = MealPlanFactory()
        MealPlanItem.objects.bulk_create(
            MealPlanItem(meal_plan=plan, meal="lunch", food=item, grams=100)
            for item in foods.values()
        )

        with django_assert_max_num_queries(4):
            auth_api(trainer).get(menu_url(plan))


class TestFoodsInUse:
    def test_a_food_in_a_menu_cannot_be_deleted(self, auth_api, nutritionist, foods):
        plan = MealPlanFactory(name="Definición")
        api = auth_api(nutritionist)
        api.put(menu_url(plan), body(("lunch", foods["rice"], 100)), format="json")

        response = api.delete(f"/api/v1/foods/{foods['rice'].id}")

        assert response.status_code == 409
        assert response.json()["code"] == "food_in_use"
        assert response.json()["plans"] == [{"id": plan.id, "name": "Definición"}]
        api.put(menu_url(plan), {"items": []}, format="json")
        assert api.delete(f"/api/v1/foods/{foods['rice'].id}").status_code == 204
        assert not Food.objects.filter(pk=foods["rice"].id).exists()


class TestClient:
    def test_the_menu_of_the_current_plan(self, auth_api, foods):
        client = active_client()
        plan = client.nutrition_plans.get(is_current=True).plan
        MealPlanItem.objects.create(meal_plan=plan, meal="dinner", food=foods["chicken"], grams=150)

        menu = auth_api(client).get("/api/v1/me/nutrition-plan/menu").json()

        assert menu["has_menu"] is True
        assert menu["meals"][2]["items"][0]["grams"] == 150

    def test_without_a_plan(self, auth_api, onboarded_client):
        response = auth_api(onboarded_client).get("/api/v1/me/nutrition-plan/menu")

        assert response.status_code == 409
        assert response.json()["code"] == "nutrition_plan_not_assigned"

    def test_shopping_list_for_some_days(self, auth_api, foods):
        client = active_client()
        current = client.nutrition_plans.get(is_current=True).plan
        MealPlanItem.objects.bulk_create(
            [
                MealPlanItem(meal_plan=current, meal="breakfast", food=foods["oats"], grams=60),
                MealPlanItem(meal_plan=current, meal="lunch", food=foods["rice"], grams=80),
                MealPlanItem(meal_plan=current, meal="dinner", food=foods["rice"], grams=70),
                MealPlanItem(meal_plan=current, meal="lunch", food=foods["chicken"], grams=150),
                MealPlanItem(meal_plan=current, meal="snacks", food=foods["apple"], grams=150),
            ]
        )

        result = auth_api(client).get("/api/v1/me/shopping-list", {"days": 3}).json()

        assert result["days"] == 3
        # By category (library order: vegetables, fruits, grains, …, meat) and then by name.
        assert [(row["food"]["name"], row["grams"]) for row in result["items"]] == [
            ("Manzana", 450),
            ("Arroz", 450),
            ("Avena", 180),
            ("Pollo", 450),
        ]

    def test_a_week_by_default_and_limits(self, auth_api):
        api = auth_api(active_client())

        empty = api.get("/api/v1/me/shopping-list").json()
        assert (empty["days"], empty["has_menu"], empty["items"]) == (7, False, [])
        for days in (0, 15):
            response = api.get("/api/v1/me/shopping-list", {"days": days})
            assert response.status_code == 400
