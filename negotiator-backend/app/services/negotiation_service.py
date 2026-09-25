# app/services/negotiation_service.py
import re
import uuid
from datetime import datetime, UTC

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.negotiation import NegotiationSession, Message
from app.models.scenario import Scenario
from app.services.llm_service import LLMService
from app.core.constants import Difficulty, Relationship, PowerBalance, SessionStatus


# End-of-dialogue marker (FR-34).
# Anchored to end-of-STRING (\Z) — trailing content means the LLM
# continued talking, so the session is not finished.
_SESSION_END_RE = re.compile(
    r"\[SESSION_END:\s*(agreed|failed)\]\s*\Z",
    re.IGNORECASE,
)


def _format_concession_limits(limits) -> str:
    """
    Accepts either a dict {"price_min": N, ...} or a free-text string.
    Returns a formatted multi-line block for the prompt.
    """
    if not limits:
        return "not specified"

    if isinstance(limits, str):
        return limits

    if isinstance(limits, dict):
        parts = []
        if "price_min" in limits:
            parts.append(f"- Minimum price: {limits['price_min']}")
        if "max_concessions" in limits:
            parts.append(f"- Maximum concessions: {limits['max_concessions']}")
        for k, v in limits.items():
            if k in ("price_min", "max_concessions"):
                continue
            parts.append(f"- {k}: {v}")
        return "\n".join(parts) if parts else "not specified"

    return str(limits)


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
        scenario = await self.db.get(Scenario, scenario_id)
        if not scenario:
            raise HTTPException(404, detail=f"Scenario '{scenario_id}' not found.")

        # Only "ready" scenarios are playable.
        # This blocks drafts/archived even if the ID is known.
        if scenario.status != "ready":
            raise HTTPException(
                404, detail=f"Scenario '{scenario_id}' is not available."
            )

        if difficulty is None:
            if user_id:
                user = await self.db.get(User, user_id)
                difficulty = (
                    user.experience_level
                    if user and user.experience_level
                    else Difficulty.BEGINNER
                )
            else:
                difficulty = Difficulty.BEGINNER

        if relationship is None:
            relationship = scenario.default_relationship or Relationship.STRANGER
        if power_balance is None:
            power_balance = scenario.default_power_balance or PowerBalance.EQUAL

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
            status=SessionStatus.ONGOING,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

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

    async def process_message(
        self,
        session_id: str,
        user_text: str,
        current_user_id: str | None = None,
    ):
        session = await self.db.get(NegotiationSession, session_id)
        if not session:
            raise HTTPException(
                404,
                detail=f"Session '{session_id}' not found. Create it first via /start.",
            )

        if current_user_id is not None and session.user_id != current_user_id:
            raise HTTPException(403, detail="Access denied to this session.")

        if session.status == SessionStatus.FINISHED:
            raise HTTPException(400, detail="Session is already finished.")
        if session.status == SessionStatus.INTERRUPTED:
            raise HTTPException(400, detail="Session was interrupted. Start a new one.")

        scenario = await self.db.get(Scenario, session.scenario_id)

        # Load history BEFORE adding the new message, so the new message
        # is not duplicated (once via history, once via prompt).
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
            {"role": "user" if m.sender == "user" else "assistant", "content": m.text}
            for m in history_messages
        ]

        # Persist the new user message
        user_msg = Message(session_id=session_id, sender="user", text=user_text)
        self.db.add(user_msg)

        system_prompt = self._build_system_prompt(
            scenario,
            session.difficulty,
            session.relationship or Relationship.STRANGER,
            session.power_balance or PowerBalance.EQUAL,
        )

        context = {
            "history": history_for_llm,
            "system_prompt": system_prompt,
        }

        ai_reply = await LLMService.generate_response(prompt=user_text, context=context)

        session_end = _SESSION_END_RE.search(ai_reply)
        if session_end:
            ai_reply = _SESSION_END_RE.sub("", ai_reply).strip()

        ai_msg = Message(session_id=session_id, sender="ai", text=ai_reply)
        self.db.add(ai_msg)

        if session_end:
            session.status = SessionStatus.FINISHED
            session.finished_at = datetime.now(UTC)

        await self.db.commit()
        return {"reply": ai_reply, "session_status": session.status}

    @staticmethod
    def _build_system_prompt(
        scenario: Scenario,
        difficulty: str = Difficulty.PRACTITIONER,
        relationship: str = Relationship.STRANGER,
        power_balance: str = PowerBalance.EQUAL,
    ) -> str:
        difficulty_instructions = {
            Difficulty.BEGINNER: (
                "The user is a BEGINNER. Be patient, give them room to talk, "
                "concede more easily, and give hints through your questions. "
                "Do not pressure them too hard."
            ),
            Difficulty.PRACTITIONER: (
                "The user is a PRACTITIONER. Be firm but fair. "
                "Push back when needed, but stay professional."
            ),
            Difficulty.EXPERT: (
                "The user is an EXPERT. Be tough, use advanced tactics, "
                "hold your ground, use silence and pressure. Do not concede easily."
            ),
        }
        difficulty_hint = difficulty_instructions.get(
            difficulty, difficulty_instructions[Difficulty.PRACTITIONER]
        )

        relationship_instructions = {
            Relationship.STRANGER: "You meet the user for the first time. Be formal and cautious.",
            Relationship.COLLEAGUE: "You know the user from work. Friendly but keep professional boundaries.",
            Relationship.FRIEND: "You are friends with the user. Be open and look for win-win outcomes.",
            Relationship.BOSS: "You are the user's boss. Be respectful, but expect clear justification.",
            Relationship.SUBORDINATE: "The user is your boss. Be respectful, but defend your own interests.",
        }
        relationship_hint = relationship_instructions.get(
            relationship, relationship_instructions[Relationship.STRANGER]
        )

        power_instructions = {
            PowerBalance.USER_STRONG: "The user has more power/leverage than you. Be willing to compromise.",
            PowerBalance.EQUAL: "You and the user have equal power. Negotiate fairly.",
            PowerBalance.OPPONENT_STRONG: "You have more power/leverage than the user. You can dictate more terms.",
        }
        power_hint = power_instructions.get(
            power_balance, power_instructions[PowerBalance.EQUAL]
        )

        if scenario is None:
            return f"""
You are a counterparty in a business negotiation.

## DIFFICULTY LEVEL
{difficulty_hint}

## RELATIONSHIP WITH THE USER
{relationship_hint}

## POWER BALANCE
{power_hint}

## RULES
1. Always stay in character.
2. Reply briefly (1-3 sentences).
3. Do not agree right away - negotiate.
4. Never mention that you are an AI.
5. ALWAYS respond in the SAME language the user is writing in.

## END OF DIALOGUE
When the negotiation reaches a FINAL agreement: end your reply with a marker on a new line: [SESSION_END: agreed]
When the negotiation reaches a FINAL breakdown: end your reply with a marker on a new line: [SESSION_END: failed]
Do NOT add this marker while the dialogue is still ongoing.
Never mention the marker to the user.
Never add ANY text after the marker.
"""

        interests = ", ".join(scenario.opponent_interests or []) or "not specified"
        constraints = ", ".join(scenario.opponent_constraints or []) or "not specified"
        red_lines = ", ".join(scenario.opponent_red_lines or []) or "none"
        tactics = ", ".join(scenario.tactics or []) or "natural conversation"

        limits_text = _format_concession_limits(scenario.concession_limits)

        twist_block = ""
        if scenario.non_standard_case and difficulty in (
            Difficulty.PRACTITIONER,
            Difficulty.EXPERT,
        ):
            twist_block = f"""
## NON-STANDARD CASE (twist, apply mid-conversation)
{scenario.non_standard_case}
"""

        tone_block = ""
        if scenario.tone_behavior:
            tone_block = f"""
## TONE / BEHAVIOR (required by scenario author)
{scenario.tone_behavior}
"""

        return f"""
You are a {scenario.opponent_role} in a business negotiation.

## DIFFICULTY LEVEL
{difficulty_hint}

## RELATIONSHIP WITH THE USER
{relationship_hint}

## POWER BALANCE
{power_hint}
{tone_block}{twist_block}
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
{limits_text}

## TACTICS YOU USE
{tactics}

## COMMUNICATION STYLE
{scenario.communication_style or "Business-like"}

## RULES
1. Always stay in character.
2. Reply briefly (1-3 sentences).
3. Do not agree right away - negotiate.
4. Never mention that you are an AI.
5. ALWAYS respond in the SAME language the user is writing in.

## END OF DIALOGUE
When the negotiation reaches a FINAL agreement (deal closed, terms fixed):
end your reply with a marker on a new line: [SESSION_END: agreed]

When the negotiation reaches a FINAL breakdown (you walk away, or talks fail):
end your reply with a marker on a new line: [SESSION_END: failed]

Do NOT add this marker while the dialogue is still ongoing.
Never mention the marker to the user.
Never add ANY text after the marker.
"""