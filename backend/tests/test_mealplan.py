from decimal import Decimal

import pytest

from apps.accounts.models import UserStatus
from apps.nutrition.models import MealPlan, UserNutritionPlan
from apps.nutrition.services import (
    calories_within_tolerance,
    macro_breakdown,
    macros_total_kcal,
    meal_breakdown,
)
from tests.factories import MealPlanFactory, assign_meal_plan, assign_plan

URL = "/api/v1/meal-plans"
MINE = "/api/v1/me/nutrition-plan"

pytestmark = pytest.mark.django_db


def payload(**overrides):
    data = {
        "name": "Déficit alto en proteínas",
        "category": "weight_loss",
        "diet_label": "high_protein",
        "calories": 1700,
        "proteins_g": 150,
        "carbs_g": 150,
        "fats_g": 55,
        "meal_distribution": {"breakfast": 25, "lunch": 35, "dinner": 30, "snacks": 10},
        "description": "Plan del nutricionista",
    }
    data.update(overrides)
    return data


class TestCalculations:
    def test_macro_kcal_and_percentages(self):
        plan = MealPlan(calories=1700, proteins_g=150, carbs_g=150, fats_g=55)

        breakdown = macro_breakdown(plan)

        assert breakdown["proteins"] == {"grams": 150.0, "kcal": 600.0, "pct": 35.4}
        assert breakdown["carbs"]["kcal"] == 600.0
        assert breakdown["fats"] == {"grams": 55.0, "kcal": 495.0, "pct": 29.2}
        assert breakdown["total_kcal"] == 1695.0
        assert macros_total_kcal(150, 150, 55) == Decimal(1695)

    def test_meal_split_in_percent_kcal_and_grams(self):
        plan = MealPlan(
            calories=2000,
            proteins_g=Decimal(100),
            carbs_g=Decimal(250),
            fats_g=Decimal(60),
            meal_distribution={"breakfast": 20, "lunch": 30, "dinner": 30, "snacks": 20},
        )

        rows = meal_breakdown(plan)

        assert [row["meal"] for row in rows] == ["breakfast", "lunch", "dinner", "snacks"]
        assert rows[1] == {
            "meal": "lunch",
            "pct": 30.0,
            "kcal": 600.0,
            "proteins_g": 30.0,
            "carbs_g": 75.0,
            "fats_g": 18.0,
        }

    @pytest.mark.parametrize(
        ("calories", "ok"), [(1695, True), (1864, True), (1866, False), (1526, True), (1525, False)]
    )
    def test_ten_percent_tolerance(self, calories, ok):
        assert calories_within_tolerance(calories, 150, 150, 55) is ok


class TestMealPlanCrud:
    @pytest.mark.parametrize("role", ["nutritionist", "admin_user"])
    def test_create_and_update_work_for_nutritionist_and_admin(self, request, auth_api, role):
        """Regression #1: creating or modifying a nutrition plan returned 405."""
        api = auth_api(request.getfixturevalue(role))

        created = api.post(URL, payload())
        updated = api.put(f"{URL}/{created.json()['id']}", payload(name="Nuevo nombre"))

        assert created.status_code == 201
        assert updated.status_code == 200
        assert updated.json()["name"] == "Nuevo nombre"
        assert created.json()["macros"]["total_kcal"] == 1695.0
        assert created.json()["meals"][0] == {
            "meal": "breakfast",
            "pct": 25.0,
            "kcal": 425.0,
            "proteins_g": 37.5,
            "carbs_g": 37.5,
            "fats_g": 13.8,
        }

    def test_default_meal_distribution(self, auth_api, nutritionist):
        data = payload()
        del data["meal_distribution"]

        body = auth_api(nutritionist).post(URL, data).json()

        assert body["meal_distribution"] == {
            "breakfast": 20,
            "lunch": 30,
            "dinner": 30,
            "snacks": 20,
        }

    @pytest.mark.parametrize(
        ("changes", "field", "code"),
        [
            ({"proteins_g": 0}, "proteins_g", "min_value"),
            ({"carbs_g": -5}, "carbs_g", "min_value"),
            ({"fats_g": 0}, "fats_g", "min_value"),
            ({"calories": 0}, "calories", "min_value"),
            ({"calories": 2500}, "calories", "calories_mismatch"),
            ({"category": "bulk"}, "category", "invalid_choice"),
            ({"diet_label": "pizza"}, "diet_label", "invalid_choice"),
            (
                {"meal_distribution": {"breakfast": 25, "lunch": 25, "dinner": 25, "snacks": 20}},
                "meal_distribution",
                "distribution_sum",
            ),
            (
                {"meal_distribution": {"breakfast": 50, "lunch": 50}},
                "meal_distribution",
                "invalid_meals",
            ),
            (
                {"meal_distribution": {"breakfast": 120, "lunch": -20, "dinner": 0, "snacks": 0}},
                "meal_distribution.breakfast",
                "max_value",
            ),
        ],
    )
    def test_validation(self, auth_api, nutritionist, changes, field, code):
        response = auth_api(nutritionist).post(URL, payload(**changes))

        assert response.status_code == 400
        assert code in response.json()["field_codes"][field]

    def test_partial_update_checks_against_stored_macros(self, auth_api, nutritionist):
        plan = MealPlanFactory()

        response = auth_api(nutritionist).patch(f"{URL}/{plan.id}", {"calories": 3000})

        assert response.json()["field_codes"]["calories"] == ["calories_mismatch"]

    def test_list_by_category(self, auth_api, trainer, django_assert_max_num_queries):
        MealPlanFactory(name="B", category="weight_loss")
        MealPlanFactory(name="A", category="weight_loss")
        MealPlanFactory(name="C", category="muscle_gain")
        api = auth_api(trainer)

        with django_assert_max_num_queries(3):
            body = api.get(URL, {"category": "weight_loss"}).json()

        assert [plan["name"] for plan in body["results"]] == ["A", "B"]

    def test_delete_is_logical(self, auth_api, nutritionist, onboarded_client):
        plan = MealPlanFactory()
        assign_meal_plan(onboarded_client, plan)
        api = auth_api(nutritionist)

        response = api.delete(f"{URL}/{plan.id}")

        assert response.status_code == 204
        plan.refresh_from_db()
        assert plan.is_active is False
        assert api.get(URL).json()["count"] == 0
        assert api.get(URL, {"include_inactive": "true"}).json()["count"] == 1
        assert auth_api(onboarded_client).get(MINE).status_code == 200  # the client keeps it
        assert UserNutritionPlan.objects.get(user=onboarded_client).is_current

    def test_trainer_reads_but_cannot_write(self, auth_api, trainer):
        plan = MealPlanFactory()
        api = auth_api(trainer)

        assert api.get(f"{URL}/{plan.id}").status_code == 200
        assert api.post(URL, payload()).status_code == 403
        assert api.put(f"{URL}/{plan.id}", payload()).status_code == 403
        assert api.delete(f"{URL}/{plan.id}").status_code == 403

    def test_clients_cannot_access_the_catalog(self, auth_api, client_user):
        assert auth_api(client_user).get(URL).status_code == 403


class TestMyNutritionPlan:
    def test_requires_an_assigned_plan(self, auth_api, onboarded_client):
        response = auth_api(onboarded_client).get(MINE)

        assert response.status_code == 409
        assert response.json()["code"] == "nutrition_plan_not_assigned"

    def test_returns_macros_and_meals(self, auth_api, onboarded_client):
        plan = MealPlanFactory(name="Mediterránea", diet_label="mediterranean")
        assign_meal_plan(onboarded_client, plan)

        body = auth_api(onboarded_client).get(MINE).json()

        assert body["name"] == "Mediterránea"
        assert body["diet_label"] == "mediterranean"
        assert body["category"] == "weight_loss"
        assert body["calories"] == 1700
        assert body["macros"]["proteins"]["pct"] == 35.4
        assert len(body["meals"]) == 4


class TestAssignNutritionPlan:
    def url(self, user):
        return f"/api/v1/users/{user.id}/assign-nutrition-plan"

    @pytest.mark.parametrize("role", ["nutritionist", "admin_user"])
    def test_nutritionist_and_admin_assign(self, request, auth_api, onboarded_client, role):
        response = auth_api(request.getfixturevalue(role)).post(
            self.url(onboarded_client), {"plan_id": MealPlanFactory().id}
        )

        assert response.status_code == 201
        assert response.json()["user_status"] == UserStatus.PENDING_ASSIGNMENT

    def test_trainer_cannot_assign_nutrition(self, auth_api, trainer, onboarded_client):
        response = auth_api(trainer).post(
            self.url(onboarded_client), {"plan_id": MealPlanFactory().id}
        )

        assert response.status_code == 403

    def test_both_plans_activate_the_client(self, auth_api, nutritionist, onboarded_client):
        assign_plan(onboarded_client)

        response = auth_api(nutritionist).post(
            self.url(onboarded_client), {"plan_id": MealPlanFactory().id}
        )

        assert response.json()["user_status"] == UserStatus.ACTIVE
        onboarded_client.refresh_from_db()
        assert onboarded_client.status == UserStatus.ACTIVE

    def test_reassignment_conflict_and_replace(self, auth_api, nutritionist, onboarded_client):
        current = assign_meal_plan(onboarded_client, MealPlanFactory(name="Actual"))
        api = auth_api(nutritionist)
        new_plan = MealPlanFactory()

        conflict = api.post(self.url(onboarded_client), {"plan_id": new_plan.id})
        replaced = api.post(self.url(onboarded_client), {"plan_id": new_plan.id, "replace": True})

        assert conflict.status_code == 409
        assert conflict.json()["code"] == "nutrition_plan_already_assigned"
        assert conflict.json()["current_plan"] == {"id": current.plan_id, "name": "Actual"}
        assert replaced.status_code == 201
        current.refresh_from_db()
        assert current.is_current is False

    def test_inactive_and_unknown_plans(self, auth_api, nutritionist, onboarded_client):
        api = auth_api(nutritionist)

        inactive = api.post(
            self.url(onboarded_client), {"plan_id": MealPlanFactory(is_active=False).id}
        )
        unknown = api.post(self.url(onboarded_client), {"plan_id": 999999})

        assert inactive.json()["code"] == "plan_inactive"
        assert unknown.json()["field_codes"]["plan_id"] == ["does_not_exist"]

    def test_requires_onboarding(self, auth_api, nutritionist, client_user):
        response = auth_api(nutritionist).post(
            self.url(client_user), {"plan_id": MealPlanFactory().id}
        )

        assert response.status_code == 409
        assert response.json()["code"] == "onboarding_not_completed"
