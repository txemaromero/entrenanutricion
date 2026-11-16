import copy
from decimal import Decimal

import pytest

from apps.accounts.models import DietPreferences, HealthInfo, User, UserDetails, UserStatus
from apps.progress.models import WeightRecord

URL = "/api/v1/me/onboarding"

pytestmark = pytest.mark.django_db

VALID = {
    "height_cm": 172,
    "initial_weight_kg": 82.5,
    "goal": "lose_weight",
    "target_weight_change_kg": 6,
    "weekly_training_days": 4,
    "daily_training_time": "1_2h",
    "physical_activity_level": "light",
    "usual_exercise_types": ["cardio", "strength"],
    "available_equipment": ["full_gym"],
    "training_preference": "gym",
    "preferences_text": "Prefiero entrenar por la tarde",
    "diet": {
        "diet_type": "omnivore",
        "food_restrictions": ["allergies"],
        "custom_food_restrictions": "Frutos secos",
        "meals_per_day": 5,
        "macronutrient_intake_self_assessment": "low_protein",
    },
    "health": {
        "medical_conditions": ["other"],
        "custom_medical_condition": "Asma leve",
        "supplements": ["protein", "omega3"],
    },
}


def payload(**changes):
    data = copy.deepcopy(VALID)
    for dotted, value in changes.items():
        target = data
        *parents, leaf = dotted.split("__")
        for key in parents:
            target = target[key]
        target[leaf] = value
    return data


class TestCompleteOnboarding:
    def test_saves_answers_and_moves_to_pending_assignment(self, auth_api, client_user):
        response = auth_api(client_user).post(URL, payload())

        assert response.status_code == 201
        body = response.json()
        assert body["target_weight_kg"] == 76.5
        assert body["diet"]["meals_per_day"] == 5
        assert body["health"]["supplements"] == ["protein", "omega3"]
        client_user.refresh_from_db()
        assert client_user.status == UserStatus.PENDING_ASSIGNMENT
        assert DietPreferences.objects.get(user=client_user).custom_food_restrictions == (
            "Frutos secos"
        )
        assert HealthInfo.objects.get(user=client_user).custom_medical_condition == "Asma leve"

    def test_creates_the_initial_weight_record(self, auth_api, client_user):
        auth_api(client_user).post(URL, payload())

        record = WeightRecord.objects.get(user=client_user)
        assert record.weight_kg == Decimal("82.5")

    def test_cannot_be_submitted_twice(self, auth_api, client_user):
        api = auth_api(client_user)
        api.post(URL, payload())

        response = api.post(URL, payload())

        assert response.status_code == 409
        assert response.json()["code"] == "onboarding_already_completed"

    def test_maintain_goal_resets_weight_change(self, auth_api, client_user):
        response = auth_api(client_user).post(URL, payload(goal="maintain"))

        assert response.json()["target_weight_change_kg"] == 0
        assert response.json()["target_weight_kg"] == 82.5

    def test_none_restriction_clears_custom_texts(self, auth_api, client_user):
        response = auth_api(client_user).post(
            URL,
            payload(diet__food_restrictions=["none"], health__medical_conditions=["diabetes"]),
        )

        assert response.json()["diet"]["custom_food_restrictions"] == ""
        assert response.json()["health"]["custom_medical_condition"] == ""

    def test_staff_cannot_onboard(self, auth_api, trainer):
        response = auth_api(trainer).post(URL, payload())

        assert response.status_code == 403
        assert response.json()["code"] == "permission_denied"

    def test_requires_authentication(self, api_client):
        assert api_client.post(URL, payload()).status_code == 401

    @pytest.mark.parametrize(
        ("changes", "field", "code"),
        [
            ({"height_cm": 99}, "height_cm", "min_value"),
            ({"height_cm": 251}, "height_cm", "max_value"),
            ({"initial_weight_kg": 29}, "initial_weight_kg", "min_value"),
            ({"initial_weight_kg": 301}, "initial_weight_kg", "max_value"),
            ({"weekly_training_days": 0}, "weekly_training_days", "min_value"),
            ({"weekly_training_days": 7}, "weekly_training_days", "max_value"),
            ({"diet__meals_per_day": 0}, "diet.meals_per_day", "min_value"),
            ({"diet__meals_per_day": 11}, "diet.meals_per_day", "max_value"),
            ({"goal": "fly"}, "goal", "invalid_choice"),
            ({"usual_exercise_types": []}, "usual_exercise_types", "min_length"),
            (
                {"usual_exercise_types": ["cardio", "cardio"]},
                "usual_exercise_types",
                "duplicated_choice",
            ),
            ({"usual_exercise_types": ["yoga"]}, "usual_exercise_types.0", "invalid_choice"),
            (
                {"available_equipment": ["no_equipment", "free_weights"]},
                "available_equipment",
                "exclusive_choice",
            ),
            (
                {"diet__food_restrictions": ["none", "allergies"]},
                "diet.food_restrictions",
                "exclusive_choice",
            ),
            (
                {"health__supplements": ["none", "protein"]},
                "health.supplements",
                "exclusive_choice",
            ),
            ({"diet__custom_food_restrictions": ""}, "diet.custom_food_restrictions", "required"),
            (
                {"health__custom_medical_condition": "  "},
                "health.custom_medical_condition",
                "required",
            ),
            ({"target_weight_change_kg": 0}, "target_weight_change_kg", "required"),
            ({"target_weight_change_kg": 60}, "target_weight_change_kg", "out_of_range"),
            ({"training_preference": "space"}, "training_preference", "invalid_choice"),
        ],
    )
    def test_validation(self, auth_api, client_user, changes, field, code):
        response = auth_api(client_user).post(URL, payload(**changes))

        assert response.status_code == 400
        assert code in response.json()["field_codes"][field]
        client_user.refresh_from_db()
        assert client_user.status == UserStatus.PENDING_ONBOARDING

    def test_gain_goal_cannot_exceed_maximum_weight(self, auth_api, client_user):
        response = auth_api(client_user).post(
            URL, payload(goal="gain_muscle", initial_weight_kg=290, target_weight_change_kg=20)
        )

        assert response.json()["field_codes"]["target_weight_change_kg"] == ["out_of_range"]


class TestReadAndUpdateOnboarding:
    def test_get_before_completing_returns_404(self, auth_api, client_user):
        response = auth_api(client_user).get(URL)

        assert response.status_code == 404
        assert response.json()["code"] == "onboarding_not_completed"

    def test_get_returns_saved_answers(self, auth_api, client_user):
        api = auth_api(client_user)
        api.post(URL, payload())

        body = api.get(URL).json()

        assert body["height_cm"] == 172
        assert body["usual_exercise_types"] == ["cardio", "strength"]
        assert body["diet"]["diet_type"] == "omnivore"
        assert body["health"]["medical_conditions"] == ["other"]

    def test_put_updates_every_section(self, auth_api, client_user):
        api = auth_api(client_user)
        api.post(URL, payload())

        response = api.put(
            URL,
            payload(
                height_cm=180,
                diet__diet_type="vegan",
                health__medical_conditions=["none"],
                health__supplements=["none"],
            ),
        )

        assert response.status_code == 200
        body = api.get(URL).json()
        assert body["height_cm"] == 180
        assert body["diet"]["diet_type"] == "vegan"
        assert body["health"]["medical_conditions"] == ["none"]
        assert body["health"]["custom_medical_condition"] == ""

    def test_put_before_completing_returns_404(self, auth_api, client_user):
        response = auth_api(client_user).put(URL, payload())

        assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_a_double_submit_gets_409_not_500(auth_api):
    from tests.concurrency import while_locked
    from tests.factories import UserFactory

    client = UserFactory()
    first_api, second_api = auth_api(client), auth_api(client)

    first, second = while_locked(
        User,
        client.pk,
        first=lambda: first_api.post(URL, payload(), format="json"),
        second=lambda: second_api.post(URL, payload(), format="json"),
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["code"] == "onboarding_already_completed"
    assert UserDetails.objects.filter(user=client).count() == 1
