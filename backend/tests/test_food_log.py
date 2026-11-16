"""Food diary of the client and its summary for the staff (phase 13)."""

import json
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.nutrition.models import FoodLogEntry, MealPlanItem
from tests.factories import FoodFactory, active_client

pytestmark = pytest.mark.django_db

URL = "/api/v1/me/food-log"


def today():
    return timezone.localdate()


@pytest.fixture
def rice():
    return FoodFactory(
        name="Arroz",
        category="grains",
        calories=Decimal("350"),
        proteins_g=Decimal("7"),
        carbs_g=Decimal("78"),
        fats_g=Decimal("1"),
    )


def log(api, food, grams=100, meal="lunch", on=None):
    payload = {
        "date": str(on or today()),
        "meal": meal,
        "food_id": food.id,
        "grams": grams,
    }
    return api.post(URL, payload, format="json")


class TestDiary:
    def test_logging_a_food_returns_the_day_with_its_totals(self, auth_api, rice):
        client = active_client()  # plan: 1700 kcal, lunch 30 %

        response = log(auth_api(client), rice, grams=150)

        assert response.status_code == 201
        day = response.json()
        assert day["target"]["calories"] == 1700
        lunch = day["meals"][1]
        assert lunch["meal"] == "lunch"
        assert lunch["target_calories"] == 510.0
        assert lunch["entries"][0] | {"id": 0} == {
            "id": 0,
            "date": str(today()),
            "meal": "lunch",
            "food_id": rice.id,
            "food_name": "Arroz",
            "grams": 150,
            "calories": 525.0,
            "proteins_g": 10.5,
            "carbs_g": 117.0,
            "fats_g": 1.5,
        }
        assert day["totals"]["calories"] == 525.0

    def test_the_logged_values_do_not_change_with_the_library(self, auth_api, rice):
        client = active_client()
        api = auth_api(client)
        log(api, rice)

        rice.calories = Decimal("10")
        rice.save()
        rice.delete()

        entry = api.get(URL).json()["meals"][1]["entries"][0]
        assert (entry["food_id"], entry["food_name"], entry["calories"]) == (None, "Arroz", 350.0)

    def test_change_grams_or_meal_and_delete(self, auth_api, rice):
        client = active_client()
        api = auth_api(client)
        entry_id = log(api, rice).json()["meals"][1]["entries"][0]["id"]

        day = api.patch(f"{URL}/{entry_id}", {"grams": 50, "meal": "dinner"}, format="json").json()

        assert day["meals"][1]["entries"] == []
        assert day["meals"][2]["entries"][0]["calories"] == 175.0
        assert day["meals"][2]["entries"][0]["grams"] == 50
        day = api.delete(f"{URL}/{entry_id}").json()
        assert day["totals"]["calories"] == 0

    def test_only_own_entries(self, auth_api, rice):
        owner, other = active_client(), active_client()
        entry_id = log(auth_api(owner), rice).json()["meals"][1]["entries"][0]["id"]

        assert auth_api(other).delete(f"{URL}/{entry_id}").status_code == 404
        assert auth_api(other).get(URL).json()["totals"]["calories"] == 0

    def test_another_day_but_not_the_future(self, auth_api, rice):
        api = auth_api(active_client())
        yesterday = today() - timedelta(days=1)
        log(api, rice, on=yesterday)

        assert api.get(URL, {"date": str(yesterday)}).json()["totals"]["calories"] == 350.0
        assert api.get(URL).json()["totals"]["calories"] == 0
        future = log(api, rice, on=today() + timedelta(days=1))
        assert future.json()["field_codes"] == {"date": ["future_date"]}
        assert api.get(URL, {"date": str(today() + timedelta(days=1))}).status_code == 400

    @pytest.mark.parametrize(("grams", "code"), [(0, "min_value"), (2001, "max_value")])
    def test_invalid_grams(self, auth_api, rice, grams, code):
        response = log(auth_api(active_client()), rice, grams=grams)

        assert response.json()["field_codes"] == {"grams": [code]}

    def test_without_a_nutrition_plan_there_is_no_target(self, auth_api, onboarded_client, rice):
        day = log(auth_api(onboarded_client), rice).json()

        assert day["target"] is None
        assert day["meals"][1]["target_calories"] is None


class TestCopyMenu:
    def test_copy_the_whole_menu_or_one_meal(self, auth_api, rice):
        client = active_client()
        plan = client.nutrition_plans.get(is_current=True).plan
        MealPlanItem.objects.create(meal_plan=plan, meal="breakfast", food=rice, grams=50)
        MealPlanItem.objects.create(meal_plan=plan, meal="lunch", food=rice, grams=100)
        api = auth_api(client)

        day = api.post(f"{URL}/copy-menu", {"date": str(today()), "meal": "lunch"}).json()
        assert [len(meal["entries"]) for meal in day["meals"]] == [0, 1, 0, 0]

        response = api.post(f"{URL}/copy-menu", {"date": str(today())})
        assert response.status_code == 201
        assert [len(meal["entries"]) for meal in response.json()["meals"]] == [1, 2, 0, 0]

    def test_nothing_to_copy(self, auth_api):
        response = auth_api(active_client()).post(f"{URL}/copy-menu", {"date": str(today())})

        assert response.status_code == 409
        assert response.json()["code"] == "menu_empty"


class TestSummary:
    def test_last_days_against_the_target(self, auth_api, rice):
        client = active_client()
        api = auth_api(client)
        log(api, rice, grams=200, on=today())  # 700 kcal
        log(api, rice, grams=100, on=today() - timedelta(days=2))  # 350 kcal
        log(api, rice, grams=100, on=today() - timedelta(days=9))  # out of the week

        summary = api.get(f"{URL}/summary").json()

        assert summary["target_calories"] == 1700
        assert len(summary["days"]) == 7
        assert summary["days"][-1]["date"] == str(today())
        assert [day["calories"] for day in summary["days"]] == [0, 0, 0, 0, 350.0, 0, 700.0]
        assert (summary["days_logged"], summary["average_calories"]) == (2, 525.0)

    def test_the_staff_sees_the_summary_of_a_client(self, auth_api, trainer, nutritionist, rice):
        client = active_client()
        log(auth_api(client), rice)
        url = f"/api/v1/users/{client.id}/food-log/summary"

        assert auth_api(nutritionist).get(url, {"days": 3}).json()["days"][-1]["calories"] == 350
        assert (
            auth_api(trainer).get(f"/api/v1/users/{trainer.id}/food-log/summary").status_code == 404
        )
        assert auth_api(client).get(url).status_code == 403

    def test_days_limits(self, auth_api):
        api = auth_api(active_client())

        assert api.get(f"{URL}/summary", {"days": 32}).status_code == 400


class TestPrivacy:
    def test_the_diary_is_exported_and_deleted_with_the_account(self, auth_api, rice):
        client = active_client()
        api = auth_api(client)
        log(api, rice, meal="dinner")

        exported = json.loads(api.get("/api/v1/me/export").content)["food_log"]
        assert exported[0] | {"date": None} == {
            "date": None,
            "meal": "dinner",
            "food": "Arroz",
            "grams": 100,
            "calories": 350.0,
            "proteins_g": 7.0,
            "carbs_g": 78.0,
            "fats_g": 1.0,
        }
        client.delete()
        assert not FoodLogEntry.objects.exists()


class TestEntriesPerDay:
    @pytest.fixture(autouse=True)
    def three_per_day(self, monkeypatch):
        from apps.nutrition import diary

        monkeypatch.setattr(diary, "MAX_ENTRIES_PER_DAY", 3)

    def test_a_day_has_a_limit(self, auth_api, rice):
        api = auth_api(active_client())
        for _ in range(3):
            assert log(api, rice).status_code == 201

        response = log(api, rice)

        assert response.status_code == 409
        assert response.json()["code"] == "food_log_day_full"
        assert log(api, rice, on=today() - timedelta(days=1)).status_code == 201

    def test_copying_the_menu_adds_all_or_nothing(self, auth_api, rice):
        client = active_client()
        api = auth_api(client)
        plan = client.nutrition_plans.get(is_current=True).plan
        for meal in ("breakfast", "lunch"):
            MealPlanItem.objects.create(meal_plan=plan, meal=meal, food=rice, grams=100)
        log(api, rice)
        log(api, rice)

        response = api.post(f"{URL}/copy-menu", {"date": str(today())})

        assert response.status_code == 409
        assert response.json()["code"] == "food_log_day_full"
        assert FoodLogEntry.objects.filter(user=client, date=today()).count() == 2


class TestDatesOfTheDiary:
    def test_up_to_five_years_back(self, auth_api, rice):
        from apps.core.utils import HISTORY_YEARS, years_before

        api = auth_api(active_client())
        oldest = years_before(today(), HISTORY_YEARS)

        assert log(api, rice, on=oldest).status_code == 201
        response = log(api, rice, on=oldest - timedelta(days=1))
        assert response.status_code == 400
        assert response.json()["field_codes"] == {"date": ["date_too_old"]}

    def test_copying_the_menu_too(self, auth_api):
        api = auth_api(active_client())

        response = api.post(f"{URL}/copy-menu", {"date": "1990-01-01"})

        assert response.json()["field_codes"] == {"date": ["date_too_old"]}

    def test_old_days_can_still_be_read(self, auth_api):
        assert auth_api(active_client()).get(URL, {"date": "1990-01-01"}).status_code == 200
