# tests/test_invites.py
"""
Tests for invite flow (FR-48, FR-49).
"""
import pytest


async def _admin_token(client, email):
    r = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": email,
            "password": "AdminPass123",
            "name": "Admin",
            "consent_given": True,
        },
    )
    return r.json()["access_token"]


async def _make_ready_case(client, admin_token, case_id):
    h = {"Authorization": f"Bearer {admin_token}"}
    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={
            "id": case_id,
            "name": "Invite Test Case",
            "description": "Test description",
            "category": "clients",
            "user_role": "Sales",
            "opponent_role": "Client",
            "user_goal": "Close the deal",
            "opponent_goal": "Get a discount",
            "tone_behavior": "Friendly",
            "concession_limits": {"price_min": 100},
        },
    )
    r = await client.post(f"/api/v1/scenarios/{case_id}/publish", headers=h)
    return r.json()["invite_code"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


# =========================
# GET /invite/{code} — public
# =========================

@pytest.mark.asyncio
async def test_preview_invite_public(client):
    at = await _admin_token(client, "prev@negotiator-ai.com")
    code = await _make_ready_case(client, at, "prev-case")

    r = await client.get(f"/api/v1/invite/{code}")
    assert r.status_code == 200
    data = r.json()
    assert data["case_id"] == "prev-case"
    assert data["name"] == "Invite Test Case"


@pytest.mark.asyncio
async def test_preview_unknown_code_returns_404(client):
    r = await client.get("/api/v1/invite/nonexistent-code-xyz")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_preview_archived_returns_410(client):
    at = await _admin_token(client, "arch-prev@negotiator-ai.com")
    h = _h(at)

    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={
            "id": "arch-prev-case",
            "name": "Archive Me",
            "description": "Test",
            "category": "clients",
            "opponent_role": "Client",
            "user_goal": "Goal",
            "opponent_goal": "Opp goal",
            "tone_behavior": "Neutral",
            "concession_limits": {"price_min": 100},
        },
    )
    pub = await client.post("/api/v1/scenarios/arch-prev-case/publish", headers=h)
    code = pub.json()["invite_code"]

    await client.post("/api/v1/scenarios/arch-prev-case/archive", headers=h)

    r = await client.get(f"/api/v1/invite/{code}")
    assert r.status_code == 410
    assert "no longer active" in r.json()["detail"].lower()


# =========================
# POST /invite/{code} — accept
# =========================

@pytest.mark.asyncio
async def test_accept_invite_creates_added_case(
    client, seeded_db, user_1_token, auth_headers_factory
):
    at = await _admin_token(client, "accept@negotiator-ai.com")
    code = await _make_ready_case(client, at, "accept-case")

    h = auth_headers_factory(user_1_token)
    r = await client.post(f"/api/v1/invite/{code}", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["case_id"] == "accept-case"
    assert data["already_added"] is False


@pytest.mark.asyncio
async def test_accept_invite_idempotent(
    client, seeded_db, user_1_token, auth_headers_factory
):
    at = await _admin_token(client, "idem@negotiator-ai.com")
    code = await _make_ready_case(client, at, "idem-case")

    h = auth_headers_factory(user_1_token)
    r1 = await client.post(f"/api/v1/invite/{code}", headers=h)
    r2 = await client.post(f"/api/v1/invite/{code}", headers=h)

    assert r1.status_code == 200
    assert r1.json()["already_added"] is False
    assert r2.status_code == 200
    assert r2.json()["already_added"] is True


@pytest.mark.asyncio
async def test_accept_invite_requires_auth(client):
    at = await _admin_token(client, "noauth@negotiator-ai.com")
    code = await _make_ready_case(client, at, "noauth-case")

    r = await client.post(f"/api/v1/invite/{code}")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_accept_invite_forbidden_for_admin(client):
    at1 = await _admin_token(client, "admin1-inv@negotiator-ai.com")
    at2 = await _admin_token(client, "admin2-inv@negotiator-ai.com")
    code = await _make_ready_case(client, at1, "admin-inv-case")

    r = await client.post(f"/api/v1/invite/{code}", headers=_h(at2))
    assert r.status_code == 403


# =========================
# GET /users/{id}/added-cases
# =========================

@pytest.mark.asyncio
async def test_added_cases_empty(
    client, seeded_db, user_1_token, auth_headers_factory
):
    h = auth_headers_factory(user_1_token)
    r = await client.get("/api/v1/users/user-1/added-cases", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["cases"] == []


@pytest.mark.asyncio
async def test_added_cases_returns_accepted(
    client, seeded_db, user_1_token, auth_headers_factory
):
    at = await _admin_token(client, "list-add@negotiator-ai.com")
    code = await _make_ready_case(client, at, "list-add-case")

    h = auth_headers_factory(user_1_token)
    await client.post(f"/api/v1/invite/{code}", headers=h)

    r = await client.get("/api/v1/users/user-1/added-cases", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["cases"][0]["case_id"] == "list-add-case"
    assert data["cases"][0]["name"] == "Invite Test Case"