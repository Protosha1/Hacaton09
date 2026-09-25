# app/api/v1/negotiation.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, UTC
from pydantic import BaseModel

from app.db.session import get_db
from app.schemas.negotiation import (
    StartNegotiationRequest,
    MessageRequest,
    AnalysisResponse,
    SessionListItem,
    SessionMessageItem,
    BriefingResponse,
)
from app.services.negotiation_service import NegotiationService
from app.services.analysis_service import AnalysisService
from app.services.voice_service import VoiceService
from app.models.negotiation import NegotiationSession, Message
from app.models.scenario import Scenario
from app.models.analysis import AnalysisReport
from app.models.user import User
from app.api.v1.auth import require_active_user
from app.core.xp import calculate_xp, is_perfect_run
from app.core.skills import update_skills_for_user
from app.core.constants import SessionStatus


router = APIRouter()


_VALID_TYPES = {"strong", "neutral", "weak"}


def _ensure_session_owner(session: NegotiationSession, user: User) -> None:
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied to this session.")


def _normalize_annotations(raw_annotations, messages_count: int) -> list[dict]:
    if not isinstance(raw_annotations, list):
        return []

    cleaned = []
    for item in raw_annotations:
        if not isinstance(item, dict):
            continue
        if "index" not in item or "original" not in item or "type" not in item:
            continue
        try:
            idx = int(item["index"])
        except (ValueError, TypeError):
            continue
        if idx < 0 or idx >= messages_count:
            continue
        ann_type = str(item.get("type", "")).lower()
        if ann_type not in _VALID_TYPES:
            continue

        suggestion = item.get("suggestion")
        if ann_type == "strong":
            suggestion = None
        elif suggestion is not None:
            suggestion = str(suggestion)

        cleaned.append({
            "index": idx,
            "original": str(item["original"]),
            "type": ann_type,
            "category": str(item.get("category", "other")),
            "why": str(item.get("why", "")),
            "suggestion": suggestion,
        })

    cleaned.sort(key=lambda a: a["index"])
    return cleaned


# =========================
# POST /negotiation/start
# =========================

@router.post("/start")
async def start_negotiation(
    req: StartNegotiationRequest,
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = NegotiationService(db)
    return await service.start_session(
        scenario_id=req.scenario_id,
        user_id=user.id,
        difficulty=req.difficulty,
        relationship=req.relationship,
        power_balance=req.power_balance,
    )


# =========================
# POST /negotiation/message
# =========================

@router.post("/message")
async def send_message(
    req: MessageRequest,
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = NegotiationService(db)
    return await service.process_message(
        req.session_id, req.message, current_user_id=user.id,
    )


# =========================
# POST /negotiation/voice
# =========================

@router.post("/voice")
async def send_voice_message(
    session_id: str = Form(...),
    audio: UploadFile = File(...),
    language: str = Form("ru"),
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    audio_bytes = await audio.read()

    try:
        user_text = await VoiceService.speech_to_text(audio_bytes, language=language)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

    service = NegotiationService(db)
    result = await service.process_message(
        session_id, user_text, current_user_id=user.id,
    )

    return {
        "user_text": user_text,
        "reply": result["reply"],
        "session_status": result["session_status"],
    }


# =========================
# POST /negotiation/{session_id}/interrupt
# =========================

@router.post("/{session_id}/interrupt")
async def interrupt_session(
    session_id: str,
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(NegotiationSession, session_id)
    if not session:
        raise HTTPException(404, detail=f"Session '{session_id}' not found")

    _ensure_session_owner(session, user)

    if session.status == SessionStatus.FINISHED:
        raise HTTPException(400, detail="Cannot interrupt a finished session.")

    if session.status != SessionStatus.INTERRUPTED:
        session.status = SessionStatus.INTERRUPTED
        session.finished_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(session)

    return {
        "session_id": session.id,
        "status": session.status,
        "finished_at": session.finished_at.isoformat() if session.finished_at else None,
    }


# =========================
# POST /negotiation/end
# =========================

@router.post("/end")
async def end_negotiation(
    session_id: str,
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(NegotiationSession, session_id)
    if not session:
        raise HTTPException(404, detail=f"Session '{session_id}' not found")

    _ensure_session_owner(session, user)

    if session.status == SessionStatus.INTERRUPTED:
        raise HTTPException(
            400, detail="Cannot finish an interrupted session. Start a new one.",
        )

    existing = await db.execute(
        select(AnalysisReport).where(AnalysisReport.session_id == session_id)
    )
    report = existing.scalar_one_or_none()
    if report:
        return _report_to_dict(report)

    msgs = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.timestamp.asc())
    )
    messages = list(msgs.scalars().all())

    user_messages = [m for m in messages if m.sender == "user"]
    if not user_messages:
        raise HTTPException(400, detail="No user messages in this session")

    scenario = await db.get(Scenario, session.scenario_id)

    session.status = SessionStatus.FINISHED
    session.finished_at = datetime.now(UTC)

    session_data = {
        "role": session.role,
        "goal": session.goal,
        "opponent": session.opponent,
        "opponent_goal": scenario.opponent_goal if scenario else None,
    }
    messages_data = [{"sender": m.sender, "text": m.text} for m in messages]

    try:
        result = await AnalysisService.analyze_session(session_data, messages_data)
    except Exception:
        await db.commit()
        raise HTTPException(500, detail="Analysis failed. Please try again.")

    scores_dict = {
        "argumentation_score": int(result.get("argumentation_score", 0)),
        "objection_handling_score": int(result.get("objection_handling_score", 0)),
        "spin_score": int(result.get("spin_score", 0)),
        "batna_score": int(result.get("batna_score", 0)),
        "emotion_control_score": int(result.get("emotion_control_score", 0)),
    }
    perfect = is_perfect_run(scores_dict)
    xp_earned = calculate_xp(
        difficulty=session.difficulty,
        verdict=result.get("goal_achieved", "no"),
        perfect=perfect,
    )

    annotations = _normalize_annotations(
        result.get("transcript_annotations"),
        messages_count=len(messages),
    )

    report = AnalysisReport(
        session_id=session_id,
        goal_achieved=result.get("goal_achieved", "unknown"),
        argumentation_score=scores_dict["argumentation_score"],
        objection_handling_score=scores_dict["objection_handling_score"],
        overall_score=int(result.get("overall_score", 0)),
        spin_score=scores_dict["spin_score"],
        batna_score=scores_dict["batna_score"],
        emotion_control_score=scores_dict["emotion_control_score"],
        spin_analysis=result.get("spin_analysis"),
        batna_analysis=result.get("batna_analysis"),
        transcript_annotations=annotations,
        xp_earned=xp_earned,
        is_perfect=perfect,
        strengths=result.get("strengths", []),
        weaknesses=result.get("weaknesses", []),
        suggestions=result.get("suggestions", []),
        full_report=result.get("full_report", ""),
    )
    db.add(report)

    if session.user_id:
        user_obj = await db.get(User, session.user_id)
        if user_obj:
            user_obj.total_xp = (user_obj.total_xp or 0) + xp_earned

    if session.user_id:
        await update_skills_for_user(db, session.user_id, scores_dict)

    try:
        await db.commit()
        await db.refresh(report)
    except IntegrityError:
        await db.rollback()
        existing = await db.execute(
            select(AnalysisReport).where(AnalysisReport.session_id == session_id)
        )
        report = existing.scalar_one()
        return _report_to_dict(report)

    return _report_to_dict(report)


# =========================
# GET /negotiation/analysis/{session_id}
# =========================

@router.get("/analysis/{session_id}", response_model=AnalysisResponse)
async def get_analysis(
    session_id: str,
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(NegotiationSession, session_id)
    if not session:
        raise HTTPException(404, detail=f"Session '{session_id}' not found")

    _ensure_session_owner(session, user)

    report = await db.execute(
        select(AnalysisReport).where(AnalysisReport.session_id == session_id)
    )
    report = report.scalar_one_or_none()
    if not report:
        raise HTTPException(
            404, detail="No analysis found. Finish the session via /end first.",
        )
    return _report_to_dict(report)


# =========================
# GET /negotiation/sessions/{user_id}
# =========================

@router.get("/sessions/{user_id}", response_model=list[SessionListItem])
async def list_user_sessions(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    if user_id != user.id:
        raise HTTPException(403, detail="You can only view your own sessions.")

    stmt = (
        select(NegotiationSession, AnalysisReport.overall_score, Scenario.name)
        .outerjoin(AnalysisReport, AnalysisReport.session_id == NegotiationSession.id)
        .outerjoin(Scenario, Scenario.id == NegotiationSession.scenario_id)
        .where(NegotiationSession.user_id == user_id)
        .order_by(NegotiationSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        SessionListItem(
            session_id=s.id,
            scenario_id=s.scenario_id,
            scenario_name=scenario_name,
            role=s.role,
            goal=s.goal,
            opponent=s.opponent,
            status=s.status,
            created_at=s.created_at,
            finished_at=s.finished_at,
            overall_score=overall_score,
        )
        for s, overall_score, scenario_name in rows
    ]


# =========================
# GET /negotiation/sessions/{session_id}/messages
# =========================

@router.get("/sessions/{session_id}/messages", response_model=list[SessionMessageItem])
async def get_session_messages(
    session_id: str,
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(NegotiationSession, session_id)
    if not session:
        raise HTTPException(404, detail=f"Session '{session_id}' not found")

    _ensure_session_owner(session, user)

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.timestamp.asc())
    )
    messages = result.scalars().all()

    return [
        SessionMessageItem(sender=m.sender, text=m.text, timestamp=m.timestamp)
        for m in messages
    ]


# =========================
# GET /negotiation/progress/{user_id}
# =========================

class UserProgressResponse(BaseModel):
    total_sessions: int
    finished_sessions: int
    average_overall: float
    average_argumentation: float
    average_objection_handling: float
    average_spin: float
    average_batna: float
    average_emotion_control: float
    goal_achieved_count: int


@router.get("/progress/{user_id}", response_model=UserProgressResponse)
async def get_user_progress(
    user_id: str,
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    if user_id != user.id:
        raise HTTPException(403, detail="You can only view your own progress.")

    stmt = (
        select(AnalysisReport)
        .join(NegotiationSession, NegotiationSession.id == AnalysisReport.session_id)
        .where(NegotiationSession.user_id == user_id)
    )
    result = await db.execute(stmt)
    reports = list(result.scalars().all())

    if not reports:
        return UserProgressResponse(
            total_sessions=0, finished_sessions=0,
            average_overall=0.0, average_argumentation=0.0,
            average_objection_handling=0.0, average_spin=0.0,
            average_batna=0.0, average_emotion_control=0.0,
            goal_achieved_count=0,
        )

    def avg(values):
        values = [v for v in values if v is not None]
        return round(sum(values) / len(values), 1) if values else 0.0

    return UserProgressResponse(
        total_sessions=len(reports),
        finished_sessions=len(reports),
        average_overall=avg([r.overall_score for r in reports]),
        average_argumentation=avg([r.argumentation_score for r in reports]),
        average_objection_handling=avg([r.objection_handling_score for r in reports]),
        average_spin=avg([r.spin_score for r in reports]),
        average_batna=avg([r.batna_score for r in reports]),
        average_emotion_control=avg([r.emotion_control_score for r in reports]),
        goal_achieved_count=sum(1 for r in reports if r.goal_achieved == "yes"),
    )


# =========================
# GET /negotiation/briefing/{scenario_id}
# =========================

@router.get("/briefing/{scenario_id}", response_model=BriefingResponse)
async def get_briefing(
    scenario_id: str,
    user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, detail=f"Scenario '{scenario_id}' not found")

    if scenario.status != "ready":
        raise HTTPException(404, detail=f"Scenario '{scenario_id}' not found")

    return BriefingResponse(
        scenario_id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        category=scenario.category,
        user_role=scenario.user_role,
        user_goal=scenario.user_goal,
        opponent_role=scenario.opponent_role,
        initial_message=scenario.initial_message,
    )


# =========================
# Helper
# =========================

def _report_to_dict(report: AnalysisReport) -> dict:
    annotations = report.transcript_annotations or []
    strong_count = sum(1 for a in annotations if isinstance(a, dict) and a.get("type") == "strong")
    weak_count = sum(1 for a in annotations if isinstance(a, dict) and a.get("type") == "weak")
    neutral_count = sum(1 for a in annotations if isinstance(a, dict) and a.get("type") == "neutral")

    return {
        "session_id": report.session_id,
        "goal_achieved": report.goal_achieved,
        "argumentation_score": report.argumentation_score,
        "objection_handling_score": report.objection_handling_score,
        "overall_score": report.overall_score,
        "spin_score": report.spin_score,
        "batna_score": report.batna_score,
        "emotion_control_score": report.emotion_control_score,
        "spin_analysis": report.spin_analysis,
        "batna_analysis": report.batna_analysis,
        "transcript_annotations": annotations,
        "strong_count": strong_count,
        "weak_count": weak_count,
        "neutral_count": neutral_count,
        "xp_earned": report.xp_earned or 0,
        "is_perfect": bool(report.is_perfect),
        "strengths": report.strengths or [],
        "weaknesses": report.weaknesses or [],
        "suggestions": report.suggestions or [],
        "full_report": report.full_report or "",
    }