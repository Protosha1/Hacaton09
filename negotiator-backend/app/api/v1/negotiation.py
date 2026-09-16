# app/api/v1/negotiation.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, UTC

from app.db.session import get_db
from app.schemas.negotiation import (
    StartNegotiationRequest, MessageRequest, AnalysisResponse,
    SessionListItem, SessionMessageItem, AnalysisListItem,
)
from app.services.negotiation_service import NegotiationService
from app.services.analysis_service import AnalysisService
from app.models.negotiation import NegotiationSession, Message
from app.models.scenario import Scenario
from app.models.analysis import AnalysisReport
from pydantic import BaseModel

router = APIRouter()


@router.post("/start")
async def start_negotiation(req: StartNegotiationRequest, db: AsyncSession = Depends(get_db)):
    service = NegotiationService(db)
    return await service.start_session(
        scenario_id=req.scenario_id,
        user_id=req.user_id,
        difficulty=req.difficulty,
        relationship=req.relationship,
        power_balance=req.power_balance,
    )


@router.post("/message")
async def send_message(req: MessageRequest, db: AsyncSession = Depends(get_db)):
    service = NegotiationService(db)
    return await service.process_message(req.session_id, req.message)


@router.post("/end")
async def end_negotiation(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Finish the negotiation and run the analysis.
    Returns the analysis report and saves it to the DB.
    """
    session = await db.get(NegotiationSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    # 2. If analysis already exists, return it
    existing = await db.execute(
        select(AnalysisReport).where(AnalysisReport.session_id == session_id)
    )
    report = existing.scalar_one_or_none()
    if report:
        return _report_to_dict(report)

    # 3. Load all messages for this session (oldest first)
    msgs = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.timestamp.asc())
    )
    messages = list(msgs.scalars().all())

    if not messages:
        raise HTTPException(status_code=400, detail="No messages in this session")

    # 4. Load scenario for context
    scenario = await db.get(Scenario, session.scenario_id)

    # 5. Mark session as finished
    session.status = "finished"
    session.finished_at = datetime.now(UTC)

    # 6. Call the analysis service
    session_data = {
        "role": session.role,
        "goal": session.goal,
        "opponent": session.opponent,
        "opponent_goal": scenario.opponent_goal if scenario else None,
    }
    messages_data = [{"sender": m.sender, "text": m.text} for m in messages]

    try:
        result = await AnalysisService.analyze_session(session_data, messages_data)
    except Exception as e:
        await db.commit()  # still save the "finished" status
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    # 7. Save the report
    report = AnalysisReport(
    session_id=session_id,
    goal_achieved=result.get("goal_achieved", "unknown"),
    argumentation_score=int(result.get("argumentation_score", 0)),
    objection_handling_score=int(result.get("objection_handling_score", 0)),
    overall_score=int(result.get("overall_score", 0)),
    spin_score=int(result.get("spin_score", 0)),                       
    batna_score=int(result.get("batna_score", 0)),                     
    emotion_control_score=int(result.get("emotion_control_score", 0)), 
    strengths=result.get("strengths", []),
    weaknesses=result.get("weaknesses", []),
    suggestions=result.get("suggestions", []),
    full_report=result.get("full_report", ""),
)
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return _report_to_dict(report)


@router.get("/analysis/{session_id}", response_model=AnalysisResponse)
async def get_analysis(session_id: str, db: AsyncSession = Depends(get_db)):
    """Return the saved analysis report for a session."""
    report = await db.execute(
        select(AnalysisReport).where(AnalysisReport.session_id == session_id)
    )
    report = report.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=404,
            detail="No analysis found. Finish the session via /end first."
        )
    return _report_to_dict(report)


def _report_to_dict(report: AnalysisReport) -> dict:
    return {
        "session_id": report.session_id,
        "goal_achieved": report.goal_achieved,
        "argumentation_score": report.argumentation_score,
        "objection_handling_score": report.objection_handling_score,
        "overall_score": report.overall_score,
        "spin_score": report.spin_score,
        "batna_score": report.batna_score,
        "emotion_control_score": report.emotion_control_score,
        "strengths": report.strengths or [],
        "weaknesses": report.weaknesses or [],
        "suggestions": report.suggestions or [],
        "full_report": report.full_report or "",
    }
# --- HISTORY ENDPOINTS ---

@router.get("/sessions/{user_id}", response_model=list[SessionListItem])
async def list_user_sessions(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return all negotiation sessions for a given user,
    including the overall score from the analysis report (if it exists).
    """
    stmt = (
        select(NegotiationSession, AnalysisReport.overall_score, Scenario.name)
        .outerjoin(AnalysisReport, AnalysisReport.session_id == NegotiationSession.id)
        .outerjoin(Scenario, Scenario.id == NegotiationSession.scenario_id)
        .where(NegotiationSession.user_id == user_id)
        .order_by(NegotiationSession.created_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        SessionListItem(
            session_id=session.id,
            scenario_id=session.scenario_id,
            scenario_name=scenario_name,
            role=session.role,
            goal=session.goal,
            opponent=session.opponent,
            status=session.status,
            created_at=session.created_at,
            finished_at=session.finished_at,
            overall_score=overall_score,
        )
        for session, overall_score, scenario_name in rows
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[SessionMessageItem])
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return all messages for a given session, oldest first.
    """
    session = await db.get(NegotiationSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.timestamp.asc())
    )
    messages = result.scalars().all()

    return [
        SessionMessageItem(
            sender=m.sender,
            text=m.text,
            timestamp=m.timestamp,
        )
        for m in messages
    ]


@router.get("/sessions/{user_id}/analysis", response_model=list[AnalysisListItem])
async def list_user_analyses(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return all analysis reports for a user, ordered by creation date.
    Useful for rendering a progress chart on the frontend.
    """
    stmt = (
        select(AnalysisReport)
        .join(NegotiationSession, NegotiationSession.id == AnalysisReport.session_id)
        .where(NegotiationSession.user_id == user_id)
        .order_by(AnalysisReport.created_at.asc())
    )
    result = await db.execute(stmt)
    reports = result.scalars().all()

    return [
        AnalysisListItem(
            session_id=r.session_id,
            overall_score=r.overall_score,
            goal_achieved=r.goal_achieved,
            created_at=r.created_at,
        )
        for r in reports
    ]
    # =========================
# User progress (FR-10, FR-11)
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
async def get_user_progress(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return aggregated progress metrics for a user across all finished sessions.

    Used for the profile page (FR-10, FR-11).
    """
    stmt = (
        select(AnalysisReport)
        .join(NegotiationSession, NegotiationSession.id == AnalysisReport.session_id)
        .where(NegotiationSession.user_id == user_id)
    )
    result = await db.execute(stmt)
    reports = list(result.scalars().all())

    if not reports:
        return UserProgressResponse(
            total_sessions=0,
            finished_sessions=0,
            average_overall=0.0,
            average_argumentation=0.0,
            average_objection_handling=0.0,
            average_spin=0.0,
            average_batna=0.0,
            average_emotion_control=0.0,
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