from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.problem import Problem
from app.schemas.problems import ProblemCreateRequest, ProblemResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("", response_model=List[ProblemResponse])
async def list_problems(
    subject: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Problem).where(Problem.visibility == "public")
    if subject:
        query = query.where(Problem.subject == subject)
    if type:
        query = query.where(Problem.type == type)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    problems = result.scalars().all()
    return [ProblemResponse.model_validate(p) for p in problems]


@router.get("/{problem_id}", response_model=ProblemResponse)
async def get_problem(problem_id: str, db: AsyncSession = Depends(get_db)):
    problem = await db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    return ProblemResponse.model_validate(problem)


@router.post("", response_model=ProblemResponse, status_code=status.HTTP_201_CREATED)
async def create_problem(
    data: ProblemCreateRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    user = await AuthService.get_current_user(request, db)
    test_cases_dict = [tc.model_dump() for tc in data.test_cases] if data.test_cases else None

    new_problem = Problem(
        title=data.title,
        statement_md=data.statement_md,
        subject=data.subject,
        difficulty_b=data.difficulty_b,
        type=data.type,
        reference_solution_md=data.reference_solution_md,
        rubric=data.rubric,
        test_cases=test_cases_dict,
        concept_ids=data.concept_ids,
        created_by=user.id,
        visibility=data.visibility,
    )
    db.add(new_problem)
    await db.commit()
    await db.refresh(new_problem)
    return ProblemResponse.model_validate(new_problem)
