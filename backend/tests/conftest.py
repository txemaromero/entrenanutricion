import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from tests import factories


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_api():
    """Build an APIClient authenticated as the given user."""

    def _build(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _build


@pytest.fixture
def client_user(db):
    return factories.UserFactory()


@pytest.fixture
def onboarded_client(db):
    return factories.onboarded_client()


@pytest.fixture
def trainer(db):
    return factories.TrainerFactory()


@pytest.fixture
def nutritionist(db):
    return factories.NutritionistFactory()


@pytest.fixture
def admin_user(db):
    return factories.AdminFactory()
