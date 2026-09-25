# tests/test_delete_scenario.py
"""
Tests for DELETE /scenarios/{id} (admin only).
"""
import pytest


async def _admin_token(client, email="deladmin@negotiator-ai.com"):
    r = await client.post(
        "/api/v1/auth/register/admin",
        json={"email": email, "password": "AdminPass123", "name": "Del Admin"},
    )
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_delete_own_scenario(client):
    token = await _admin_token(client)
    h = _h(token)

    # Create
    await client.post(
        "/api/v1/scenarios/",
        headers=h,
        json={"id": "to-delete", "name": "Will be deleted"},
    )

    # Delete
    r = await client.delete("/api/v1/scenarios/to-delete", headers=h)
    assert r.status_code == 204

    # Verify gone
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
async def test_delete_detaches_sessions(client, seeded_db, user_1_token, auth_headers_factory, mock_llm):
    """Deleting a scenario does not delete sessions - it sets scenario_id = NULL."""
    at = await _admin_token(client, "detach@negotiator-ai.com")
    ah = _h(at)

    # Admin creates scenario (different from seeded scenario-1)
    await client.post(
        "/api/v1/scenarios/",
        headers=ah,
        json={
            "id": "detach-case",
            "name": "Detach Case",
            "tone_behavior": "Neutral",
            "concession_limits": {"price_min": 100},
        },
    )

    # User starts a session on it
    uh = auth_headers_factory(user_1_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=uh,
        json={"scenario_id": "detach-case", "user_id": "user-1"},
    )
    assert r.status_code == 200

    # Admin deletes scenario
    r = await client.delete("/api/v1/scenarios/detach-case", headers=ah)
    assert r.status_code == 204

    # Session history is preserved
    r = await client.get("/api/v1/negotiation/sessions/user-1", headers=uh)
    assert r.status_code == 200
    assert len(r.json()) >= 1