# app/services/negotiation_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
import uuid
from datetime import datetime, UTC

from app.models.user import User
from app.models.negotiation import NegotiationSession, Message
from app.models.scenario import Scenario
from app.services.llm_service import LLMService


class NegotiationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_session(
        self,
        scenario_id: str,
        user_id: str = None,
        difficulty: str = None,
        relationship: str = None,
        power_balance: str = None,
    ):
        # 1. Load the scenario
        scenario = await self.db.get(Scenario, scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario '{scenario_id}' not found.",
            )

        # 2. Determine difficulty (FR-14)
        if difficulty is None:
            if user_id:
                user = await self.db.get(User, user_id)
                difficulty = (
                    user.experience_level
                    if user and user.experience_level
                    else "beginner"
                )
            else:
                difficulty = "beginner"

        # 3. Relationship & power balance (FR-12) — fallback to scenario defaults
        if relationship is None:
            relationship = scenario.default_relationship or "stranger"
        if power_balance is None:
            power_balance = scenario.default_power_balance or "equal"

        # 4. Create the session
        session = NegotiationSession(
            id=str(uuid.uuid4()),
            scenario_id=scenario.id,
            user_id=user_id,
            role=scenario.user_role,
            goal=scenario.user_goal,
            opponent=scenario.opponent_role,
            difficulty=difficulty,
            relationship=relationship,
            power_balance=power_balance,
            status="ongoing",
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # 5. Save the opponent's opening message
        first_msg = Message(
            session_id=session.id,
            sender="ai",
            text=scenario.initial_message or "Hello. Let's begin.",
        )
        self.db.add(first_msg)
        await self.db.commit()

        return {
            "session_id": session.id,
            "role": session.role,
            "goal": session.goal,
            "opponent": session.opponent,
            "difficulty": session.difficulty,
            "relationship": session.relationship,
            "power_balance": session.power_balance,
            "first_message": scenario.initial_message or "Hello. Let's begin.",
        }

    async def process_message(self, session_id: str, user_text: str):
        # 1. Load the session
        session = await self.db.get(NegotiationSession, session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found. Create it first via /start.",
            )
        if session.status == "finished":
            raise HTTPException(
                status_code=400,
                detail="Session is already finished.",
            )

        # 2. Load the scenario
        scenario = await self.db.get(Scenario, session.scenario_id)

        # 3. Save the user's message
        user_msg = Message(session_id=session_id, sender="user", text=user_text)
        self.db.add(user_msg)
        await self.db.flush()

        # 4. Load recent history (last 20 messages, oldest first)
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.timestamp.desc())
            .limit(20)
        )
        result = await self.db.execute(stmt)
        history_messages = list(result.scalars().all())
        history_messages.reverse()

        history_for_llm = [
            {
                "role": "user" if m.sender == "user" else "assistant",
                "content": m.text,
            }
            for m in history_messages
        ]

        # 5. Build the system prompt with all context
        system_prompt = self._build_system_prompt(
            scenario,
            session.difficulty,
            session.relationship or "stranger",
            session.power_balance or "equal",
        )

        context = {
            "history": history_for_llm,
            "system_prompt": system_prompt,
        }

        # 6. Call the LLM
        ai_reply = await LLMService.generate_response(
            prompt=user_text, context=context
        )

        # 7. Save the AI reply
        ai_msg = Message(session_id=session_id, sender="ai", text=ai_reply)
        self.db.add(ai_msg)

        # 8. Check for finishing signals
        lowered = ai_reply.lower()
        if any(
            word in lowered
            for word in ["deal", "agreed", "we have a deal", "sign the contract"]
        ):
            session.status = "finished"
            session.finished_at = datetime.now(UTC)

        await self.db.commit()

        return {"reply": ai_reply, "session_status": session.status}

    @staticmethod
    def _build_system_prompt(
        scenario: Scenario,
        difficulty: str = "practitioner",
        relationship: str = "stranger",
        power_balance: str = "equal",
    ) -> str:
        """Build the LLM system prompt from scenario + session context."""

        # --- Difficulty (FR-14) ---
        difficulty_instructions = {
            "beginner": (
                "The user is a BEGINNER. Be patient, give them room to talk, "
                "concede more easily, and give hints through your questions. "
                "Do not pressure them too hard."
            ),
            "practitioner": (
                "The user is a PRACTITIONER. Be firm but fair. "
                "Push back when needed, but stay professional."
            ),
            "expert": (
                "The user is an EXPERT. Be tough, use advanced tactics, "
                "hold your ground, use silence and pressure. "
                "Do not concede easily."
            ),
        }
        difficulty_hint = difficulty_instructions.get(
            difficulty, difficulty_instructions["practitioner"]
        )

        # --- Relationship (FR-12) ---
        relationship_instructions = {
            "stranger": "You meet the user for the first time. Be formal and cautious.",
            "colleague": "You know the user from work. Friendly but keep professional boundaries.",
            "friend": "You are friends with the user. Be open and look for win-win outcomes.",
            "boss": "You are the user's boss. Be respectful, but expect clear justification for their requests.",
            "subordinate": "The user is your boss. Be respectful, but defend your own interests.",
        }
        relationship_hint = relationship_instructions.get(
            relationship, relationship_instructions["stranger"]
        )

        # --- Power balance (FR-12) ---
        power_instructions = {
            "user_strong": "The user has more power/leverage than you. Be willing to compromise.",
            "equal": "You and the user have equal power. Negotiate fairly.",
            "opponent_strong": "You have more power/leverage than the user. You can dictate more of the terms.",
        }
        power_hint = power_instructions.get(
            power_balance, power_instructions["equal"]
        )

        # --- Fallback if scenario is missing ---
        if scenario is None:
            return (
                f"You are a counterparty in a business negotiation. "
                f"{difficulty_hint} {relationship_hint} {power_hint} "
                f"Stay in character and respond naturally."
            )

        # --- Scenario details ---
        interests = ", ".join(scenario.opponent_interests or []) or "not specified"
        constraints = ", ".join(scenario.opponent_constraints or []) or "not specified"
        red_lines = ", ".join(scenario.opponent_red_lines or []) or "none"
        tactics = ", ".join(scenario.tactics or []) or "natural conversation"

        limits = scenario.concession_limits or {}
        price_min = limits.get("price_min", "unknown")
        max_concessions = limits.get("max_concessions", "unknown")

        return f"""
You are a {scenario.opponent_role} in a business negotiation.

## DIFFICULTY LEVEL
{difficulty_hint}

## RELATIONSHIP WITH THE USER
{relationship_hint}

## POWER BALANCE
{power_hint}

## YOUR CHARACTER
{scenario.opponent_character or "Professional negotiator"}

## YOUR GOAL
{scenario.opponent_goal or "Get the best terms"}

## YOUR HIDDEN INTERESTS
{interests}

## YOUR CONSTRAINTS
{constraints}

## WHAT ANNOYS YOU
{red_lines}

## CONCESSION LIMITS
- Minimum price: {price_min}
- Maximum concessions: {max_concessions}

## TACTICS YOU USE
{tactics}

## COMMUNICATION STYLE
{scenario.communication_style or "Business-like"}

## RULES
1. Always stay in character.
2. Reply briefly (1-3 sentences).
3. Do not agree right away - negotiate.
4. Never mention that you are an AI.
5. Never offer a price below {price_min}.
6. ALWAYS respond in the SAME language the user is writing in.
"""