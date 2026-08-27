import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.config.test_settings")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("CASE_NO_KEY_POLICY", "item_only")

import pytest
from fastapi.testclient import TestClient

from fastapi_app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def registered_user(client):
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "StrongPass123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    return {
        "payload": payload,
        "token": body["access_token"],
        "headers": {"Authorization": f"Bearer {body['access_token']}"},
        "user": body["user"],
    }
