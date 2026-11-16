"""Food library (phase 9): catalog per 100 g with calories, macros and micronutrients."""

import pytest

from apps.nutrition.models import Food
from tests.factories import FoodFactory, active_client

FOODS = "/api/v1/foods"

pytestmark = pytest.mark.django_db


def payload(**overrides):
    data = {
        "name": "Lentejas",
        "category": "legumes",
        "calories": 352,
        "proteins_g": 24.6,
        "carbs_g": 63,
        "fats_g": 1.1,
        "fiber_g": 10.7,
        "sugars_g": 2,
        "iron_mg": 6.5,
        "potassium_mg": 677,
    }
    data.update(overrides)
    return data


def field_codes(response) -> dict:
    return response.json().get("field_codes", {})


class TestRead:
    def test_everyone_signed_in_can_browse_it(self, auth_api, trainer):
        FoodFactory(name="Brócoli")
        for user in (active_client(), trainer):
            response = auth_api(user).get(FOODS)
            assert response.status_code == 200
            assert [food["name"] for food in response.json()["results"]] == ["Brócoli"]

    def test_anonymous_users_cannot(self, api_client):
        assert api_client.get(FOODS).status_code == 401

    def test_detail_includes_micronutrients_and_macro_split(self, auth_api, nutritionist):
        food = FoodFactory(
            name="Lentejas",
            calories=352,
            proteins_g=24.6,
            carbs_g=63,
            fats_g=1.1,
            iron_mg=6.5,
            vitamin_c_mg=None,
        )

        body = auth_api(nutritionist).get(f"{FOODS}/{food.id}").json()

        assert body["iron_mg"] == 6.5
        assert body["vitamin_c_mg"] is None
        # Same calculation as the meal plans: % over the kcal of the macros.
        assert body["macros"]["proteins"] == {"grams": 24.6, "kcal": 98.0, "pct": 27.3}
        assert body["macros"]["carbs"]["pct"] == 69.9
        assert body["macros"]["total_kcal"] == 360.0

    def test_search_category_and_ordering(self, auth_api, nutritionist):
        FoodFactory(name="Manzana", category="fruits", calories=52)
        FoodFactory(name="Plátano", category="fruits", calories=89)
        FoodFactory(name="Almendras", category="nuts_seeds", calories=579)
        api = auth_api(nutritionist)

        def names(params):
            return [food["name"] for food in api.get(FOODS, params).json()["results"]]

        assert names({"category": "fruits"}) == ["Manzana", "Plátano"]
        assert names({"search": "almen"}) == ["Almendras"]
        assert names({"ordering": "-calories"}) == ["Almendras", "Plátano", "Manzana"]

    def test_unknown_category_is_rejected(self, auth_api, nutritionist):
        response = auth_api(nutritionist).get(FOODS, {"category": "sweets"})

        assert response.status_code == 400

    def test_list_query_budget(self, auth_api, nutritionist, django_assert_max_num_queries):
        FoodFactory.create_batch(15)
        api = auth_api(nutritionist)

        with django_assert_max_num_queries(3):
            response = api.get(FOODS)

        assert response.json()["count"] == 15


class TestWrite:
    def test_nutritionist_creates_a_food(self, auth_api, nutritionist):
        response = auth_api(nutritionist).post(FOODS, payload(name="  Lentejas  "), format="json")

        assert response.status_code == 201, response.content
        body = response.json()
        assert body["name"] == "Lentejas"
        assert body["fiber_g"] == 10.7
        assert body["vitamin_d_ug"] is None
        assert Food.objects.get().potassium_mg == 677

    def test_admin_updates_and_deletes(self, auth_api, admin_user):
        food = FoodFactory()
        api = auth_api(admin_user)

        response = api.patch(f"{FOODS}/{food.id}", {"vitamin_c_mg": 89.2}, format="json")
        assert response.status_code == 200
        assert response.json()["vitamin_c_mg"] == 89.2

        assert api.delete(f"{FOODS}/{food.id}").status_code == 204
        assert not Food.objects.exists()

    @pytest.mark.parametrize("role", ["trainer", "client"])
    def test_trainers_and_clients_cannot_edit(self, auth_api, role, trainer):
        user = trainer if role == "trainer" else active_client()
        food = FoodFactory()
        api = auth_api(user)

        assert api.post(FOODS, payload(), format="json").status_code == 403
        assert api.patch(f"{FOODS}/{food.id}", {"name": "X"}, format="json").status_code == 403
        assert api.delete(f"{FOODS}/{food.id}").status_code == 403

    def test_names_are_unique_ignoring_case(self, auth_api, nutritionist):
        FoodFactory(name="Lentejas")

        response = auth_api(nutritionist).post(FOODS, payload(name="LENTEJAS"), format="json")

        assert field_codes(response) == {"name": ["food_name_taken"]}

    def test_renaming_a_food_to_its_own_name_is_fine(self, auth_api, nutritionist):
        food = FoodFactory(name="Lentejas")

        response = auth_api(nutritionist).patch(
            f"{FOODS}/{food.id}", {"name": "lentejas"}, format="json"
        )

        assert response.status_code == 200

    def test_macros_cannot_exceed_100_grams(self, auth_api, nutritionist):
        response = auth_api(nutritionist).post(
            FOODS, payload(proteins_g=40, carbs_g=50, fats_g=11), format="json"
        )

        assert response.status_code == 400
        assert response.json()["code"] == "macros_exceed_100g"

    @pytest.mark.parametrize(
        ("overrides", "field", "code"),
        [
            ({"sugars_g": 70}, "sugars_g", "sugars_exceed_carbs"),
            ({"saturated_fat_g": 2}, "saturated_fat_g", "saturated_exceed_fats"),
            ({"proteins_g": -1}, "proteins_g", "min_value"),
            ({"fats_g": 101}, "fats_g", "max_value"),
            ({"calories": 950}, "calories", "max_value"),
            ({"iron_mg": -0.5}, "iron_mg", "min_value"),
            ({"category": "sweets"}, "category", "invalid_choice"),
            ({"name": ""}, "name", "blank"),
        ],
    )
    def test_validation(self, auth_api, nutritionist, overrides, field, code):
        response = auth_api(nutritionist).post(FOODS, payload(**overrides), format="json")

        assert response.status_code == 400
        assert code in field_codes(response)[field]

    def test_partial_updates_are_checked_against_stored_values(self, auth_api, nutritionist):
        food = FoodFactory(carbs_g=6.6, sugars_g=1.7)

        response = auth_api(nutritionist).patch(
            f"{FOODS}/{food.id}", {"sugars_g": 7}, format="json"
        )

        assert field_codes(response) == {"sugars_g": ["sugars_exceed_carbs"]}

    def test_calories_are_required(self, auth_api, nutritionist):
        data = payload()
        del data["calories"]

        response = auth_api(nutritionist).post(FOODS, data, format="json")

        assert field_codes(response) == {"calories": ["required"]}
