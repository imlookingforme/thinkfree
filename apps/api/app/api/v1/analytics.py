from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analytics import DailyStats, Mastery
from app.models.concept import Concept, ConceptEdge
from app.models.problem import Problem
from app.models.session import Session, Validation
from app.services.auth_service import AuthService
from app.services.scoring_service import ScoringService

router = APIRouter()


# --- Pydantic Schemas ---

class MetricExplainability(BaseModel):
    name: str
    symbol: str
    formula: str
    plain_english: str
    inputs: Dict[str, Any]
    value: float


class FreeThinkerRadar(BaseModel):
    unaided_success_rate: float
    explanation_coverage: float
    persistence_effort: float
    spaced_retention: float
    consistency_score: float


class DashboardOverviewResponse(BaseModel):
    student_id: str
    its: float
    adr: float
    ewma_reliance_7d: float
    ewma_reliance_30d: float
    self_solves_count: int
    ai_assisted_count: int
    self_solve_rate: float
    current_streak: int
    peak_study_hour: int
    flow_minutes_7d: int
    active_minutes_7d: int
    radar: FreeThinkerRadar
    explainability: Dict[str, MetricExplainability]


class ConceptMasteryItem(BaseModel):
    concept_id: str
    name: str
    subject: str
    parent_id: Optional[str]
    p_known: float
    mastery_band: str  # "struggling" (<0.4), "developing" (0.4-0.7), "mastered" (>=0.7)
    ease: float
    interval_days: float
    next_review_at: Optional[datetime]
    prerequisites_unmet: List[str]


class ConceptMasteryResponse(BaseModel):
    concepts: List[ConceptMasteryItem]
    weak_concepts: List[ConceptMasteryItem]


class ReviewQueueItem(BaseModel):
    concept_id: str
    concept_name: str
    p_known: float
    ease: float
    interval_days: float
    due_status: str  # "overdue", "due_today", "upcoming"
    recommended_problem_id: Optional[str] = None
    recommended_problem_title: Optional[str] = None


class SpacedReviewResponse(BaseModel):
    total_due: int
    items: List[ReviewQueueItem]


class ExplainabilityResponse(BaseModel):
    metrics: Dict[str, MetricExplainability]


# --- Helper Functions ---

async def update_student_mastery_and_stats(
    db: AsyncSession,
    student_id: str,
    problem: Problem,
    session: Session,
    validation_passed: bool,
    validation_coverage: float
) -> None:
    """
    Hook called when a session completes: updates BKT mastery for associated concepts,
    calculates SM-2 review dates, and records/updates daily_stats.
    """
    now = datetime.now()
    today = date.today()

    # 1. Update BKT & SM-2 for all concepts mapped to this problem
    concept_ids = problem.concept_ids or []
    quality_score = 5 if (validation_passed and session.help_cost == 0.0) else (
        4 if (validation_passed and session.help_cost <= 0.35) else (
            3 if validation_passed else 1
        )
    )

    for cid in concept_ids:
        res = await db.execute(
            select(Mastery).where(Mastery.student_id == student_id, Mastery.concept_id == cid)
        )
        mastery = res.scalar_one_or_none()
        if not mastery:
            mastery = Mastery(
                student_id=student_id,
                concept_id=cid,
                p_known=0.30,
                ease=2.5,
                interval_days=1.0,
                updated_at=now
            )
            db.add(mastery)

        # Bayesian Knowledge Tracing update
        mastery.p_known = ScoringService.update_bkt(
            p_known=mastery.p_known,
            is_correct=validation_passed,
            help_cost=session.help_cost
        )
        mastery.updated_at = now

        # SM-2 update
        new_interval, new_ef, next_rev = ScoringService.update_sm2(
            interval_days=mastery.interval_days,
            ease_factor=mastery.ease,
            quality_score=quality_score
        )
        mastery.interval_days = new_interval
        mastery.ease = new_ef
        mastery.next_review_at = next_rev

    # 2. Daily Stats accumulation
    res_ds = await db.execute(
        select(DailyStats).where(DailyStats.student_id == student_id, DailyStats.date == today)
    )
    daily_stat = res_ds.scalar_one_or_none()
    if not daily_stat:
        daily_stat = DailyStats(
            student_id=student_id,
            date=today,
            active_minutes=0,
            flow_minutes=0,
            self_solves=0,
            ai_assisted=0,
            its=0.0,
            adr=0.0
        )
        db.add(daily_stat)

    session_duration_min = 0
    if session.ended_at and session.started_at:
        session_duration_min = max(1, int((session.ended_at - session.started_at).total_seconds() / 60.0))

    daily_stat.active_minutes += session_duration_min
    if session.help_cost == 0.0:
        daily_stat.self_solves += 1
        daily_stat.flow_minutes += session_duration_min
    else:
        daily_stat.ai_assisted += 1

    # Recalculate ADR for today
    p_reliance = ScoringService.calculate_problem_reliance(
        session.help_cost,
        unlocked_via_stuck=(session.unlock_reason == "stuck_declared")
    )
    # Simple weighted blend
    total_sessions_today = daily_stat.self_solves + daily_stat.ai_assisted
    daily_stat.adr = round((daily_stat.adr * (total_sessions_today - 1) + p_reliance) / total_sessions_today, 4)

    await db.commit()


# --- Endpoints ---

@router.get("/dashboard", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Computes dashboard metrics: ITS, ADR, EWMA reliance, self-solve rate,
    streaks, radar dimensions, and mathematical explainability cards.
    """
    user = await AuthService.get_current_user(request, db)

    # 1. Fetch recent 60 days of DailyStats
    cutoff_60d = date.today() - timedelta(days=60)
    res_ds = await db.execute(
        select(DailyStats)
        .where(DailyStats.student_id == user.id, DailyStats.date >= cutoff_60d)
        .order_by(DailyStats.date.asc())
    )
    stats_list = list(res_ds.scalars().all())

    # 2. Fetch completed sessions
    res_sessions = await db.execute(
        select(Session)
        .where(Session.student_id == user.id, Session.state == "done")
        .order_by(Session.ended_at.desc())
        .limit(100)
    )
    sessions = list(res_sessions.scalars().all())

    total_self_solves = sum(s.self_solves for s in stats_list)
    total_ai_assisted = sum(s.ai_assisted for s in stats_list)
    total_solves = total_self_solves + total_ai_assisted
    self_solve_rate = round((total_self_solves / total_solves * 100.0), 1) if total_solves > 0 else 100.0

    # Calculate Problem Reliance history & EWMA
    reliance_history: List[float] = []
    effort_history: List[float] = []
    for s in reversed(sessions):
        rel = ScoringService.calculate_problem_reliance(
            help_cost=s.help_cost,
            unlocked_via_stuck=(s.unlock_reason == "stuck_declared")
        )
        reliance_history.append(rel)
        effort_history.append(s.effort_score or 0.0)

    adr_val = ScoringService.calculate_adr(reliance_history[-30:] if reliance_history else [0.0])
    ewma_series = ScoringService.calculate_ewma_reliance(reliance_history) if reliance_history else [0.0]
    ewma_7d = ewma_series[-1] if len(ewma_series) >= 1 else 0.0
    ewma_30d = (sum(ewma_series[-30:]) / len(ewma_series[-30:])) if len(ewma_series) >= 1 else 0.0

    # 3. Calculate Validations / Coverage
    res_vals = await db.execute(
        select(Validation)
        .join(Session, Validation.session_id == Session.id)
        .where(Session.student_id == user.id)
        .order_by(Validation.created_at.desc())
        .limit(50)
    )
    vals = list(res_vals.scalars().all())
    mean_cov = 0.85
    if vals:
        cov_list = []
        for v in vals:
            if isinstance(v.rubric_scores, list):
                s_sum = sum(item.get("score", 0.0) for item in v.rubric_scores)
                cov_list.append(s_sum / len(v.rubric_scores) if v.rubric_scores else 0.8)
        if cov_list:
            mean_cov = sum(cov_list) / len(cov_list)

    # 4. Spaced retention from Mastery
    res_mastery = await db.execute(
        select(Mastery).where(Mastery.student_id == user.id)
    )
    masteries = list(res_mastery.scalars().all())
    spaced_retention = 0.80
    if masteries:
        spaced_retention = sum(m.p_known for m in masteries) / len(masteries)

    persistence_effort = (sum(effort_history) / len(effort_history)) if effort_history else 0.75
    unaided_ratio = (total_self_solves / total_solves) if total_solves > 0 else 0.90

    # 5. ITS
    its_val = ScoringService.calculate_its(
        unaided_success_rate=unaided_ratio,
        mean_validation_coverage=mean_cov,
        persistence_effort=persistence_effort,
        spaced_retention=spaced_retention
    )

    # 6. Streak
    active_days = [s.date for s in stats_list if s.self_solves > 0]
    streak_val = ScoringService.calculate_streak(active_days)

    # 7. Flow & Active minutes (last 7 days)
    last_7d_stats = stats_list[-7:] if stats_list else []
    flow_min_7d = sum(s.flow_minutes for s in last_7d_stats)
    active_min_7d = sum(s.active_minutes for s in last_7d_stats)

    # Peak study hour heuristic
    peak_hr = 16  # 4 PM default
    if sessions:
        hours = [s.started_at.hour for s in sessions if s.started_at]
        if hours:
            from collections import Counter
            peak_hr = Counter(hours).most_common(1)[0][0]

    # Explainability dictionary with exact formulas
    explainability_data = {
        "ITS": MetricExplainability(
            name="Independent Thinking Score",
            symbol="ITS",
            formula="100 × (0.30·U + 0.30·V + 0.20·P + 0.20·Q)",
            plain_english="Synthesizes your unaided success (30%), explanation coverage (30%), persistence before asking AI (20%), and retention over spaced reviews (20%).",
            inputs={
                "U (unaided success)": round(unaided_ratio, 3),
                "V (explanation coverage)": round(mean_cov, 3),
                "P (persistence effort)": round(persistence_effort, 3),
                "Q (spaced retention)": round(spaced_retention, 3)
            },
            value=its_val
        ),
        "ADR": MetricExplainability(
            name="AI Dependency Ratio",
            symbol="ADR",
            formula="(1/N) × Σ min(1.0, help_cost / 1.5)",
            plain_english="Average fraction of AI ladder assistance used across your last 30 problem sessions. Lower is better.",
            inputs={
                "window_size_N": min(30, len(reliance_history)),
                "mean_help_cost": round(sum(s.help_cost for s in sessions[:30]) / max(1, len(sessions[:30])), 2) if sessions else 0.0,
                "h_cap": 1.5
            },
            value=adr_val
        ),
        "EWMA": MetricExplainability(
            name="EWMA Reliance (Trend)",
            symbol="R_t",
            formula="0.2·r_t + 0.8·R_{t-1}",
            plain_english="Exponentially smoothed reliance showing whether your independence is accelerating this week.",
            inputs={
                "lambda": 0.2,
                "latest_r": round(reliance_history[-1], 3) if reliance_history else 0.0,
                "previous_ewma": round(ewma_series[-2], 3) if len(ewma_series) > 1 else 0.0
            },
            value=ewma_7d
        )
    }

    return DashboardOverviewResponse(
        student_id=user.id,
        its=its_val,
        adr=adr_val,
        ewma_reliance_7d=ewma_7d,
        ewma_reliance_30d=ewma_30d,
        self_solves_count=total_self_solves,
        ai_assisted_count=total_ai_assisted,
        self_solve_rate=self_solve_rate,
        current_streak=streak_val,
        peak_study_hour=peak_hr,
        flow_minutes_7d=flow_min_7d,
        active_minutes_7d=active_min_7d,
        radar=FreeThinkerRadar(
            unaided_success_rate=round(unaided_ratio, 2),
            explanation_coverage=round(mean_cov, 2),
            persistence_effort=round(persistence_effort, 2),
            spaced_retention=round(spaced_retention, 2),
            consistency_score=0.88
        ),
        explainability=explainability_data
    )


@router.get("/mastery", response_model=ConceptMasteryResponse)
async def get_concept_mastery(
    request: Request,
    subject: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns Bayesian Knowledge Tracing (BKT) mastery for concepts,
    identifying weak areas (<0.40) and alerting on unmet prerequisites.
    """
    user = await AuthService.get_current_user(request, db)

    # 1. Fetch concepts
    concept_query = select(Concept)
    if subject:
        concept_query = concept_query.where(Concept.subject == subject)
    res_c = await db.execute(concept_query)
    all_concepts = list(res_c.scalars().all())

    # 2. Fetch prerequisite edges
    res_edges = await db.execute(select(ConceptEdge).where(ConceptEdge.kind == "prereq"))
    prereq_edges = list(res_edges.scalars().all())
    # dst_concept_id requires src_concept_id
    prereq_map: Dict[str, List[str]] = {}
    for edge in prereq_edges:
        prereq_map.setdefault(edge.dst_concept_id, []).append(edge.src_concept_id)

    # 3. Fetch Student's Mastery
    res_m = await db.execute(select(Mastery).where(Mastery.student_id == user.id))
    mastery_dict = {m.concept_id: m for m in res_m.scalars().all()}

    concept_items: List[ConceptMasteryItem] = []
    weak_items: List[ConceptMasteryItem] = []

    for c in all_concepts:
        m = mastery_dict.get(c.id)
        p_known = m.p_known if m else 0.30
        ease = m.ease if m else 2.5
        interval = m.interval_days if m else 1.0
        next_rev = m.next_review_at if m else None

        band = "mastered" if p_known >= 0.70 else ("developing" if p_known >= 0.40 else "struggling")

        # Check unmet prerequisites
        unmet: List[str] = []
        required_srcs = prereq_map.get(c.id, [])
        for req_id in required_srcs:
            req_mastery = mastery_dict.get(req_id)
            if not req_mastery or req_mastery.p_known < 0.60:
                unmet.append(req_id)

        item = ConceptMasteryItem(
            concept_id=c.id,
            name=c.name,
            subject=c.subject,
            parent_id=c.parent_id,
            p_known=round(p_known, 3),
            mastery_band=band,
            ease=round(ease, 2),
            interval_days=round(interval, 1),
            next_review_at=next_rev,
            prerequisites_unmet=unmet
        )
        concept_items.append(item)
        if p_known < 0.40:
            weak_items.append(item)

    return ConceptMasteryResponse(
        concepts=concept_items,
        weak_concepts=weak_items
    )


@router.get("/reviews", response_model=SpacedReviewResponse)
async def get_spaced_reviews(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns today's spaced review queue based on SM-2 due dates.
    Pairs each due concept with a recommended problem variant.
    """
    user = await AuthService.get_current_user(request, db)
    now = datetime.now()

    # Query mastery items where next_review_at is due or null
    res_m = await db.execute(
        select(Mastery)
        .where(Mastery.student_id == user.id)
        .order_by(Mastery.next_review_at.asc())
    )
    masteries = list(res_m.scalars().all())

    # Map concept names
    res_c = await db.execute(select(Concept))
    concepts = {c.id: c.name for c in res_c.scalars().all()}

    # Map a problem for each concept
    res_probs = await db.execute(select(Problem).limit(50))
    all_probs = list(res_probs.scalars().all())

    items: List[ReviewQueueItem] = []
    for m in masteries:
        status_str = "upcoming"
        if not m.next_review_at or m.next_review_at <= now:
            status_str = "overdue"
        elif m.next_review_at <= now + timedelta(hours=24):
            status_str = "due_today"

        # Find matching problem
        rec_p = next((p for p in all_probs if p.concept_ids and m.concept_id in p.concept_ids), None)

        if status_str in ("overdue", "due_today"):
            items.append(ReviewQueueItem(
                concept_id=m.concept_id,
                concept_name=concepts.get(m.concept_id, m.concept_id),
                p_known=round(m.p_known, 3),
                ease=round(m.ease, 2),
                interval_days=round(m.interval_days, 1),
                due_status=status_str,
                recommended_problem_id=rec_p.id if rec_p else None,
                recommended_problem_title=rec_p.title if rec_p else None
            ))

    return SpacedReviewResponse(
        total_due=len(items),
        items=items
    )


@router.get("/explainability", response_model=ExplainabilityResponse)
async def get_explainability_reference(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns transparency formulas and definitions for all student KPIs.
    """
    dash = await get_dashboard_overview(request, db)
    return ExplainabilityResponse(metrics=dash.explainability)
