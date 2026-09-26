# tests/test_delete_scenario.py
"""
Tests for DELETE /scenarios/{id} (admin only).
"""
import pytest


async def _admin_token(client, email="deladmin@negotiator-ai.com"):
    r = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": email,
            "password": "AdminPass123",
            "name": "Del Admin",
            "consent_given": True,
        },
    )
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


async def _make_published_case(client, admin_token, case_id):
    """Create + publish a case so it's playable."""
    h = _h(admin_token)
    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={
            "id": case_id,
            "name": "Test Case",
            "description": "Description",
            "category": "clients",
            "opponent_role": "Client",
            "user_goal": "Goal",
            "opponent_goal": "Opp goal",
            "tone_behavior": "Neutral",
            "concession_limits": {"price_min": 100},
        },
    )
    pub = await client.post(f"/api/v1/scenarios/{case_id}/publish", headers=h)
    return pub.json()["invite_code"]


@pytest.mark.asyncio
async def test_delete_own_scenario(client):
    token = await _admin_token(client)
    h = _h(token)

    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={"id": "to-delete", "name": "Will be deleted"},
    )

    r = await client.delete("/api/v1/scenarios/to-delete", headers=h)
    assert r.status_code == 204

    r = await client.get("/api/v1/scenarios/to-delete")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_other_admin_forbidden(client):
    t1 = await _admin_token(client, "owner-del@negotiator-ai.com")
    t2 = await _admin_token(client, "thief-del@negotiator-ai.com")

    await client.post(
        "/api/v1/scenarios/",
        headers=_h(t1),
        json={"id": "protected-del", "name": "Protected"},
    )

    r = await client.delete("/api/v1/scenarios/protected-del", headers=_h(t2))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_delete_unknown_scenario(client):
    token = await _admin_token(client, "unk-del@negotiator-ai.com")
    r = await client.delete("/api/v1/scenarios/ghost", headers=_h(token))
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_detaches_sessions(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm
):
    """Deleting a scenario does not delete sessions - it sets scenario_id = NULL."""
    at = await _admin_token(client, "detach@negotiator-ai.com")
    ah = _h(at)

    await _make_published_case(client, at, "detach-case")

    # User starts a session on it
    uh = auth_headers_factory(user_1_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=uh,
        json={"scenario_id": "detach-case"},
    )
    assert r.status_code == 200

    # Admin deletes scenario
    r = await client.delete("/api/v1/scenarios/detach-case", headers=ah)
    assert r.status_code == 204

    # Session history is preserved
    r = await client.get("/api/v1/negotiation/sessions/user-1", headers=uh)
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_delete_removes_user_added_cases(
    client, seeded_db, user_1_token, auth_headers_factory
):
    """Deleting a scenario also removes UserAddedCase links (FK cleanup)."""
    at = await _admin_token(client, "fk-del@negotiator-ai.com")
    ah = _h(at)
    code = await _make_published_case(client, at, "fk-case")

    # User accepts invite
    uh = auth_headers_factory(user_1_token)
    await client.post(f"/api/v1/invite/{code}", headers=uh)

    # Verify link exists
    r = await client.get("/api/v1/users/user-1/added-cases", headers=uh)
    assert r.json()["total"] == 1

    # Delete scenario
    await client.delete("/api/v1/scenarios/fk-case", headers=ah)

    # Link must be gone
    r = await client.get("/api/v1/users/user-1/added-cases", headers=uh)
    assert r.json()["total"] == 0