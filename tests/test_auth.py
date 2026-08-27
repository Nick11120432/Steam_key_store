import pytest

from shared.models import User


@pytest.mark.django_db(transaction=True)
def test_register_hashes_password_and_returns_jwt(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "bob"

    user = User.objects.get(username="bob")
    assert user.password != "StrongPass123!"
    assert user.check_password("StrongPass123!")


@pytest.mark.django_db(transaction=True)
def test_login(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "carol",
            "email": "carol@example.com",
            "password": "StrongPass123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "carol", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]
