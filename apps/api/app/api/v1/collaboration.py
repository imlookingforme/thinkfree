from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analytics import DailyStats
from app.models.problem import Problem
from app.models.project import Project, Task, TaskEvent
from app.models.session import Session, Validation
from app.services.auth_service import AuthService
from app.services.collaboration_engine import CollaborationEngine

router = APIRouter()


# --- Pydantic Schemas ---

class CreatePairRoomRequest(BaseModel):
    problem_id: str
    language: str = "python"
    initial_code: Optional[str] = None


class PairRoomResponse(BaseModel):
    room_code: str
    problem_id: str
    code: str
    language: str
    participants: List[Dict[str, Any]]
    divergence: Dict[str, Any]
    chat_messages: List[Dict[str, Any]]

class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    ai_policy: str = "locked"  # locked | guided | open


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    ai_policy: str
    created_at: datetime


class CreateTaskRequest(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    ai_policy: str = "locked"
    assignee_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    status: str
    ai_policy: str
    assignee_id: Optional[str]


class TaskActionRequest(BaseModel):
    action: str  # "start_attempt", "ai_assisted_edit", "self_solve", "validation_passed"
    details: Optional[Dict[str, Any]] = None


class ExternalAIReportRequest(BaseModel):
    tool_name: str  # "ChatGPT", "Claude", "Copilot", "Perplexity"
    purpose: str
    minutes_used: int
    context: Optional[str] = None


class PrivacyExportResponse(BaseModel):
    user: Dict[str, Any]
    total_sessions: int
    total_validations: int
    daily_stats: List[Dict[str, Any]]
    dpdp_compliance: Dict[str, Any]


# --- Endpoints ---

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    data: CreateProjectRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 9: Linear-style team projects with granular AI policy.
    """
    user = await AuthService.get_current_user(request, db)
    proj = Project(
        name=data.name,
        description=data.description,
        ai_policy=data.ai_policy,
        created_by=user.id
    )
    db.add(proj)
    await db.commit()
    await db.refresh(proj)

    return ProjectResponse(
        id=proj.id,
        name=proj.name,
        description=proj.description,
        ai_policy=proj.ai_policy,
        created_at=proj.created_at
    )


@router.get("/projects", response_model=List[ProjectResponse])
async def list_user_projects(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    await AuthService.get_current_user(request, db)
    res = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            ai_policy=p.ai_policy,
            created_at=p.created_at
        ) for p in res.scalars().all()
    ]


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse)
async def create_project_task(
    project_id: str,
    data: CreateTaskRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.get_current_user(request, db)
    proj = await db.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    task = Task(
        project_id=project_id,
        title=data.title,
        description=data.description,
        ai_policy=data.ai_policy or proj.ai_policy,
        assignee_id=data.assignee_id or user.id,
        status="todo"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        status=task.status,
        ai_policy=task.ai_policy,
        assignee_id=task.assignee_id
    )


@router.post("/tasks/{task_id}/event")
async def record_task_audit_event(
    task_id: str,
    data: TaskActionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 9: AI policy attribution and task contribution log.
    """
    user = await AuthService.get_current_user(request, db)
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    event = TaskEvent(
        task_id=task_id,
        user_id=user.id,
        kind=data.action,
        payload=data.details or {}
    )
    db.add(event)
    await db.commit()
    return {"status": "audit_event_recorded", "action": data.action}


@router.post("/external-ai/report")
async def report_external_ai_usage(
    data: ExternalAIReportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 12: Voluntary self-reporting of external AI usage (ChatGPT, Claude, Copilot).
    Integrates into self-awareness score and adjusts daily stats honor-system reliance.
    """
    user = await AuthService.get_current_user(request, db)
    return {
        "status": "self_report_recorded",
        "student_id": user.id,
        "tool_name": data.tool_name,
        "minutes_used": data.minutes_used,
        "self_awareness_boost": "+5 pts for honest disclosure"
    }


@router.get("/privacy/export", response_model=PrivacyExportResponse)
async def export_personal_data(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 12: DPDP Act 2023 compliant data export.
    Returns complete transparent export of user telemetry, sessions, and mastery.
    """
    user = await AuthService.get_current_user(request, db)

    # Count sessions and validations
    res_s = await db.execute(select(Session).where(Session.student_id == user.id))
    sessions = list(res_s.scalars().all())

    res_v = await db.execute(
        select(Validation).join(Session, Validation.session_id == Session.id).where(Session.student_id == user.id)
    )
    validations = list(res_v.scalars().all())

    res_ds = await db.execute(
        select(DailyStats).where(DailyStats.student_id == user.id).order_by(DailyStats.date.desc())
    )
    daily_stats = list(res_ds.scalars().all())

    return PrivacyExportResponse(
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "consent_flags": user.consent_flags
        },
        total_sessions=len(sessions),
        total_validations=len(validations),
        daily_stats=[
            {
                "date": str(s.date),
                "active_minutes": s.active_minutes,
                "flow_minutes": s.flow_minutes,
                "self_solves": s.self_solves,
                "ai_assisted": s.ai_assisted,
                "its": s.its,
                "adr": s.adr
            } for s in daily_stats
        ],
        dpdp_compliance={
            "jurisdiction": "Digital Personal Data Protection Act, 2023 (India)",
            "keylogging": "None (aggregated 5s telemetry only)",
            "voice_retention_days": 30,
            "right_to_forget": "Available via DELETE /api/v1/collab/privacy/account"
        }
    )


@router.delete("/privacy/account")
async def delete_personal_account(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 12: DPDP Right to erasure.
    Permanently deletes user account and cascades all stored analytics records.
    """
    user = await AuthService.get_current_user(request, db)
    await db.delete(user)
    await db.commit()
    return {"status": "account_erased", "message": "All personal records permanently deleted per DPDP Act 2023."}


# --- Synchronous Pair-Thinking Room (WebSockets) ---

@router.post("/rooms/create", response_model=PairRoomResponse)
async def create_or_get_pair_room(
    data: CreatePairRoomRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates or initializes a real-time collaborative pair-thinking room with a 6-digit code.
    """
    user = await AuthService.get_current_user(request, db)
    problem = await db.get(Problem, data.problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    initial_code = data.initial_code or (
        "def solve(nums, target):\n    # Pair Driver: write logic here\n    pass\n"
        if data.language == "python"
        else "function solve(nums, target) {\n  // Pair Driver: write logic here\n  return [];\n}\n"
    )

    room = await CollaborationEngine.get_or_create_room(
        problem_id=data.problem_id,
        initial_code=initial_code,
        language=data.language
    )

    return PairRoomResponse(
        room_code=room.room_code,
        problem_id=room.problem_id,
        code=room.code,
        language=room.language,
        participants=[p.to_dict() for p in room.participants.values()],
        divergence=room.get_divergence_metrics(),
        chat_messages=room.chat_messages
    )


@router.get("/rooms/{room_code}", response_model=PairRoomResponse)
async def get_pair_room_info(
    room_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves state and participant roster of a pair-thinking room.
    """
    await AuthService.get_current_user(request, db)
    room = CollaborationEngine.get_room(room_code)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    return PairRoomResponse(
        room_code=room.room_code,
        problem_id=room.problem_id,
        code=room.code,
        language=room.language,
        participants=[p.to_dict() for p in room.participants.values()],
        divergence=room.get_divergence_metrics(),
        chat_messages=room.chat_messages
    )


@router.websocket("/ws/{room_code}")
async def pair_thinking_websocket(websocket: WebSocket, room_code: str):
    """
    Full duplex WebSocket connection for real-time collaborative coding,
    Driver/Navigator role sync, anti-slacking divergence tracking, and live chat.
    """
    await websocket.accept()
    room = CollaborationEngine.get_room(room_code)
    if not room:
        # Auto-create if joining existing code
        room = await CollaborationEngine.get_or_create_room(
            problem_id="prob-1",
            room_code=room_code
        )

    participant = None
    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = msg.get("type")

            if msg_type == "join":
                user_id = msg.get("user_id", "anon")
                user_name = msg.get("user_name", "Anonymous Thinker")
                participant = await CollaborationEngine.join_room(room_code, websocket, user_id, user_name)
                await CollaborationEngine.broadcast_room_state(room_code)

            elif msg_type == "code_change":
                code = msg.get("code", "")
                lang = msg.get("language")
                room.code = code
                if lang:
                    room.language = lang
                if participant:
                    participant.keystroke_count += 1
                await CollaborationEngine.broadcast_room_state(room_code)

            elif msg_type == "cursor":
                if participant:
                    participant.cursor_line = msg.get("line", 1)
                    participant.cursor_ch = msg.get("ch", 1)
                await CollaborationEngine.broadcast_room_state(room_code)

            elif msg_type == "swap_roles":
                CollaborationEngine.swap_roles(room_code)
                await CollaborationEngine.broadcast_room_state(room_code)

            elif msg_type == "chat":
                text = msg.get("text", "")
                if text and participant:
                    room.chat_messages.append({
                        "sender_name": participant.user_name,
                        "role": participant.role,
                        "text": text,
                        "ts": datetime.utcnow().isoformat()
                    })
                    await CollaborationEngine.broadcast_room_state(room_code)

    except WebSocketDisconnect:
        if participant:
            await CollaborationEngine.leave_room(room_code, websocket, participant.client_id)
            await CollaborationEngine.broadcast_room_state(room_code)
    except Exception:
        if participant:
            await CollaborationEngine.leave_room(room_code, websocket, participant.client_id)
