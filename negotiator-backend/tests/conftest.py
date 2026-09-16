# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User
from app.models.scenario import Scenario


# In-memory SQLite for tests -- no files, no side effects
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """Fresh in-memory DB engine per test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine):
    """Session to the test DB."""
    SessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def seeded_db(test_db):
    """Test DB with one user and one scenario."""
    user = User(id="user-1", email="test@example.com", name="Test")
    scenario = Scenario(
        id="scenario-1",
        name="Tough Buyer",
        description="Test scenario",
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
async def client(test_db):
    """
    FastAPI test client.
    Overrides the real get_db dependency with the test DB.
    """
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    # --- MOCKS ---

@pytest.fixture
def mock_llm(monkeypatch):
    """
    Replace LLMService.generate_response with a canned reply.
    Use by adding 'mock_llm' to a test's arguments.
    """
    from app.services import llm_service

    async def fake_generate(prompt: str, context: dict = None) -> str:
        return f"[MOCKED LLM] You said: {prompt}"

    monkeypatch.setattr(
        llm_service.LLMService, "generate_response", fake_generate
    )


@pytest.fixture
def mock_analysis(monkeypatch):
    """
    Replace AnalysisService.analyze_session with a canned report.
    """
    from app.services import analysis_service

    async def fake_analyze(session_data, messages):
        return {
            "goal_achieved": "yes",
            "argumentation_score": 80,
            "objection_handling_score": 75,
            "overall_score": 78,
            "strengths": ["Good opening"],
            "weaknesses": ["Conceded too fast"],
            "suggestions": ["Anchor higher"],
            "full_report": "Mock report.",
        }

    monkeypatch.setattr(
        analysis_service.AnalysisService, "analyze_session", fake_analyze
    )