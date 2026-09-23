# tests/test_auth_v8.py
"""
Tests for auth v8 features.
"""
import pytest
from sqlalchemy import select

from app.models.user import User


# =========================
# 1. User registration
# =========================

@pytest.mark.asyncio
async def test_register_user_success(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "Secret1234",
            "name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_user_short_password_rejected(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
            "name": "Short Pass",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_user_duplicate_email(client, seeded_db):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "Secret1234",
            "name": "Duplicate",
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_user_has_pending_onboarding_status(client, test_db):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "pending@example.com",
            "password": "Secret1234",
            "name": "Pending",
        },
    )

    result = await test_db.execute(
        select(User).where(User.email == "pending@example.com")
    )
    user = result.scalar_one()
    assert user.role == "user"
    assert user.status == "pending_onboarding"
    assert user.onboarding_completed is False
    assert user.total_xp == 0


# =========================
# 2. User login
# =========================

@pytest.mark.asyncio
async def test_login_user_success(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "Secret1234",
            "name": "Login User",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "Secret1234"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "Secret1234",
            "name": "Wrong Pass",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "WrongPass1"},
    )
    assert response.status_code == 401


# =========================
# 3. Onboarding
# =========================

@pytest.mark.asyncio
async def test_onboarding_changes_status_to_active(client, test_db):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "onboard@example.com",
            "password": "Secret1234",
            "name": "Onboard",
        },
    )
    token = reg.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/onboarding",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "directions": ["management", "clients"],
            "experience_level": "practitioner",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["onboarding_completed"] is True
    assert data["directions"] == ["management", "clients"]
    assert data["experience_level"] == "practitioner"


@pytest.mark.asyncio
async def test_onboarding_invalid_direction(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "baddir@example.com",
            "password": "Secret1234",
            "name": "Bad Dir",
        },
    )
    token = reg.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/onboarding",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "directions": ["unknown_category"],
            "experience_level": "beginner",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_onboarding_too_many_directions(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "toomany@example.com",
            "password": "Secret1234",
            "name": "Too Many",
        },
    )
    token = reg.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/onboarding",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "directions": ["management", "clients", "team", "hiring"],
            "experience_level": "beginner",
        },
    )
    assert response.status_code == 422


# =========================
# 4. Admin registration
# =========================

@pytest.mark.asyncio
async def test_register_admin_success(client, test_db):
    response = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "newadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "New Admin",
        },
    )
    assert response.status_code == 201
    assert "access_token" in response.json()

    result = await test_db.execute(
        select(User).where(User.email == "newadmin@negotiator-ai.com")
    )
    user = result.scalar_one()
    assert user.role == "admin"
    assert user.status == "active"
    assert user.onboarding_completed is True


@pytest.mark.asyncio
async def test_register_admin_short_password(client):
    response = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "shortadmin@negotiator-ai.com",
            "password": "short",
            "name": "Short Admin",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_admin_duplicate_email(client, seeded_db):
    response = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "test@example.com",
            "password": "AdminPass123",
            "name": "Duplicate Admin",
        },
    )
    assert response.status_code == 400


# =========================
# 5. Admin login
# =========================

@pytest.mark.asyncio
async def test_login_admin_success(client):
    await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "loginadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Login Admin",
        },
    )

    response = await client.post(
        "/api/v1/auth/login/admin",
        json={"email": "loginadmin@negotiator-ai.com", "password": "AdminPass123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_admin_rejects_regular_user(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "regular@example.com",
            "password": "Secret1234",
            "name": "Regular",
        },
    )

    response = await client.post(
        "/api/v1/auth/login/admin",
        json={"email": "regular@example.com", "password": "Secret1234"},
    )
    assert response.status_code == 403
    assert "not an administrator" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_admin_wrong_password(client):
    await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "wrongadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Wrong Admin",
        },
    )

    response = await client.post(
        "/api/v1/auth/login/admin",
        json={"email": "wrongadmin@negotiator-ai.com", "password": "WrongPass1"},
    )
    assert response.status_code == 401


# =========================
# 6. /auth/me
# =========================

@pytest.mark.asyncio
async def test_me_returns_new_fields(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "mefields@example.com",
            "password": "Secret1234",
            "name": "Me Fields",
        },
    )
    token = reg.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "user"
    assert data["status"] == "pending_onboarding"
    assert data["total_xp"] == 0
    assert data["onboarding_completed"] is False


@pytest.mark.asyncio
async def test_me_without_token(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


# =========================
# 7. Role-based access
# =========================

@pytest.mark.asyncio
async def test_me_forbidden_for_admin(client):
    reg = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "forbiddenadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Forbidden Admin",
        },
    )
    token = reg.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert "administrator" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_onboarding_forbidden_for_admin(client):
    reg = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "adminonb@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Admin Onboarding",
        },
    )
    token = reg.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/onboarding",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "directions": ["management"],
            "experience_level": "beginner",
        },
    )
    assert response.status_code == 403