import pytest


@pytest.mark.django_db
def test_health_endpoint_reports_ok(api_client):
    response = api_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_openapi_schema_is_served(api_client, db):
    response = api_client.get("/api/schema/")

    assert response.status_code == 200
    assert b"entrenanutricion API" in response.content
