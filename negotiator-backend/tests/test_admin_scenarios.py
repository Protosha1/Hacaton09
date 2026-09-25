# tests/test_admin_scenarios.py
"""
Tests for admin scenario constructor (FR-43, FR-45, FR-46, FR-47, FR-48).
"""
import pytest


# =========================
# Helpers
# =========================

async def _admin_token(client, email="admin-scen@negotiator-ai.com"):
    r = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": email,
            "password": "AdminPass123",
            "name": "Scen Admin",
            "consent_given": True,
        },
    )
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _ready_payload(**overrides):
    """Full set of fields required for publish."""
    base = {
        "name": "Ready Case",
        "description": "Full description",
        "category": "clients",
        "opponent_role": "Client",
        "user_goal": "Close the deal",
        "opponent_goal": "Get a discount",
        "tone_behavior": "Friendly",
        "concession_limits": {"price_min": 100},
    }
    base.update(overrides)
    return base


# =========================
# POST /scenarios/ creates draft
# =========================

@pytest.mark.asyncio
async def test_create_scenario_is_draft(client):
    token = await _admin_token(client)
    h = _headers(token)

    r = await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={
            "id": "my-case-1",
            "name": "My Case",
            "category": "clients",
            "opponent_role": "Client",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["id"] == "my-case-1"
    assert data["status"] == "draft"
    assert data["invite_code"] is None
    assert data["admin_id"] is not None


@pytest.mark.asyncio
async def test_create_scenario_requires_admin(client, user_token):
    """Regular user -> 403."""
    h = _headers(user_token)
    r = await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={"name": "Hack"},
    )
    assert r.status_code == 403


# =========================
# GET /scenarios/my
# =========================

@pytest.mark.asyncio
async def test_my_scenarios_empty(client):
    token = await _admin_token(client, "emptyadmin@negotiator-ai.com")
    r = await client.get("/api/v1/scenarios/my", headers=_headers(token))
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_my_scenarios_only_mine(client):
    t1 = await _admin_token(client, "admin-a@negotiator-ai.com")
    t2 = await _admin_token(client, "admin-b@negotiator-ai.com")

    await client.post(
        "/api/v1/scenarios/",
        headers=_headers(t1),
        json={"id": "a-case", "name": "A Case"},
    )
    await client.post(
        "/api/v1/scenarios/",
        headers=_headers(t2),
        json={"id": "b-case", "name": "B Case"},
    )

    r = await client.get("/api/v1/scenarios/my", headers=_headers(t1))
    ids = [s["id"] for s in r.json()]
    assert "a-case" in ids
    assert "b-case" not in ids


# =========================
# POST /scenarios/{id}/publish
# =========================

@pytest.mark.asyncio
async def test_publish_missing_all_fields(client):
    token = await _admin_token(client, "publisher@negotiator-ai.com")
    h = _headers(token)

    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={"id": "pub-case", "name": "Pub"},
    )

    r = await client.post("/api/v1/scenarios/pub-case/publish", headers=h)
    assert r.status_code == 400
    detail = r.json()["detail"].lower()
    assert "category" in detail
    assert "tone_behavior" in detail
    assert "concession_limits" in detail


@pytest.mark.asyncio
async def test_publish_missing_only_step2_fields(client):
    """Step 1 filled, Step 2 not."""
    token = await _admin_token(client, "publisher-mid@negotiator-ai.com")
    h = _headers(token)

    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={
            "id": "pub-mid",
            "name": "Pub Mid",
            "description": "desc",
            "category": "clients",
            "opponent_role": "Client",
            "user_goal": "goal",
            "opponent_goal": "opp goal",
        },
    )

    r = await client.post("/api/v1/scenarios/pub-mid/publish", headers=h)
    assert r.status_code == 400
    detail = r.json()["detail"].lower()
    assert "tone_behavior" in detail
    assert "concession_limits" in detail


@pytest.mark.asyncio
async def test_publish_success(client):
    token = await _admin_token(client, "publisher2@negotiator-ai.com")
    h = _headers(token)

    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json=_ready_payload(id="ready-case"),
    )

    r = await client.post("/api/v1/scenarios/ready-case/publish", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert data["invite_code"]
    assert data["invite_url"].startswith("/invite/")


@pytest.mark.asyncio
async def test_publish_forbidden_for_other_admin(client):
    t1 = await _admin_token(client, "owner@negotiator-ai.com")
    t2 = await _admin_token(client, "stranger@negotiator-ai.com")

    await client.post(
        "/api/v1/scenarios/",
        headers=_headers(t1),
        json=_ready_payload(id="owner-case"),
    )

    r = await client.post(
        "/api/v1/scenarios/owner-case/publish",
        headers=_headers(t2),
    )
    assert r.status_code == 403


# =========================
# POST /scenarios/{id}/archive
# =========================

@pytest.mark.asyncio
async def test_archive_scenario(client):
    token = await _admin_token(client, "archiver@negotiator-ai.com")
    h = _headers(token)

    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json=_ready_payload(id="arch-case"),
    )
    await client.post("/api/v1/scenarios/arch-case/publish", headers=h)

    r = await client.post("/api/v1/scenarios/arch-case/archive", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "archived"


# =========================
# Public catalog filters
# =========================

@pytest.mark.asyncio
async def test_public_catalog_hides_admin_cases(client, seeded_db):
    """Admin creates + publishes a case. It should NOT appear in GET /scenarios/."""
    token = await _admin_token(client, "hider@negotiator-ai.com")
    h = _headers(token)

    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json=_ready_payload(id="hidden-case", category="clients"),
    )
    await client.post("/api/v1/scenarios/hidden-case/publish", headers=h)

    r = await client.get("/api/v1/scenarios/")
    ids = [s["id"] for s in r.json()]
    assert "hidden-case" not in ids
    assert "scenario-1" in ids


# =========================
# PUT
# =========================

@pytest.mark.asyncio
async def test_update_own_scenario(client):
    token = await _admin_token(client, "updater@negotiator-ai.com")
    h = _headers(token)

    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={"id": "upd-case", "name": "Old Name"},
    )

    r = await client.put(
        "/api/v1/scenarios/upd-case",
        headers=h,
        json={"name": "New Name", "tone_behavior": "Tough"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "New Name"
    assert data["tone_behavior"] == "Tough"


@pytest.mark.asyncio
async def test_update_other_admin_forbidden(client):
    t1 = await _admin_token(client, "owner2@negotiator-ai.com")
    t2 = await _admin_token(client, "thief@negotiator-ai.com")

    await client.post(
        "/api/v1/scenarios/",
        headers=_headers(t1),
        json={"id": "protected-case", "name": "Protected"},
    )

    r = await client.put(
        "/api/v1/scenarios/protected-case",
        headers=_headers(t2),
        json={"name": "Stolen"},
    )
    assert r.status_code == 403