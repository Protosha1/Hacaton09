# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User
from app.models.scenario import Scenario
from app.core.security import create_access_token


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """
    Single in-memory SQLite shared by all sessions.
    StaticPool ensures all sessions use the same connection,
    so seeded data is visible to HTTP requests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine):
    """Direct session — for seeding in fixtures."""
    SessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def seeded_db(test_db):
    """Test DB with one user (id='user-1') and one scenario (id='scenario-1')."""
    user = User(id="user-1", email="test@example.com", name="Test")
    scenario = Scenario(
        id="scenario-1",
        name="Tough Buyer",
        description="Test scenario",
        status="ready",
        admin_id=None,
        user_role="Seller",
        user_goal="Sell at $1000+",
        opponent_role="Buyer",
        opponent_character="Tough",
        opponent_goal="Buy at $900",
        opponent_interests=["fast delivery"],
        opponent_constraints=["needs approval"],
        opponent_red_lines=["rudeness"],
        concession_limits={"price_min": 900, "max_concessions": 3},
        tactics=["anchor_low"],
        communication_style="Business-like",
        initial_message="Hello. What is your price?",
    )
    test_db.add(user)
    test_db.add(scenario)
    await test_db.commit()
    return test_db


@pytest_asyncio.fixture
async def client(test_engine):
    """
    FastAPI client with session-per-request, like in production.
    Uses the same in-memory DB via StaticPool.
    """
    SessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# =========================
# Auth helpers
# =========================

@pytest_asyncio.fixture
async def user_token(client):
    """Register a regular user and return JWT."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "Secret1234",
            "name": "Test User",
        },
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def user_1_token(seeded_db):
    """JWT for seeded user-1."""
    return create_access_token({"sub": "user-1"})


@pytest.fixture
def auth_headers_factory():
    def _make(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}
    return _make


# =========================
# Mocks
# =========================

@pytest.fixture
def mock_llm(monkeypatch):
    from app.services import llm_service

    async def fake_generate(prompt: str, context: dict = None) -> str:
        return f"[MOCKED LLM] You said: {prompt}"

    monkeypatch.setattr(
        llm_service.LLMService, "generate_response", fake_generate
    )


@pytest.fixture
def mock_analysis(monkeypatch):
    from app.services import analysis_service

    async def fake_analyze(session_data, messages):
        return {
            "goal_achieved": "yes",
            "argumentation_score": 80,
            "objection_handling_score": 75,
            "overall_score": 78,
            "spin_score": 70,
            "batna_score": 65,
            "emotion_control_score": 85,
            "strengths": ["Good opening"],
            "weaknesses": ["Conceded too fast"],
            "suggestions": ["Anchor higher"],
            "full_report": "Mock report.",
        }

    monkeypatch.setattr(
        analysis_service.AnalysisService, "analyze_session", fake_analyze
    )