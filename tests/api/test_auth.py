import pytest


def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "role": "STAFF",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "STAFF"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client, test_users):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "unique_name",
            "email": "admin@test.com",
            "password": "StrongPassword123!",
            "role": "STAFF",
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["message"]


def test_register_duplicate_username(client, test_users):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "test_admin",
            "email": "unique_email@test.com",
            "password": "StrongPassword123!",
            "role": "STAFF",
        },
    )
    assert response.status_code == 409
    assert "already taken" in response.json()["message"]


def test_login_success(client, test_users):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "test_admin",
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "ADMIN"
    assert data["username"] == "test_admin"


def test_login_invalid_password(client, test_users):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "test_admin",
            "password": "WrongPassword999!",
        },
    )
    assert response.status_code == 401
    assert "Invalid username/email or password" in response.json()["message"]


def test_login_inactive_user(client, test_users):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "inactive_user",
            "password": "Password123!",
        },
    )
    assert response.status_code == 401
    assert "inactive" in response.json()["message"]


def test_get_current_user_me(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "test_admin"
    assert data["role"] == "ADMIN"


def test_get_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
