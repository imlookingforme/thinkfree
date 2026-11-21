import os
from typing import AsyncGenerator

import pytest

# Set test environment and test in-memory SQLite before loading app config
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.problem import Problem

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def sample_problem() -> Problem:
    async with TestSessionLocal() as session:
        problem = Problem(
            id="test-prob-1",
            title="Two Sum Problem",
            statement_md="Find two numbers that add up to target.",
            subject="Programming Basics",
            difficulty_b=1.0,
            type="coding",
            reference_solution_md="def two_sum(nums, target): return []",
            rubric={"correctness": "passes test cases"},
            test_cases=[{"input": "[2, 7]\n9", "expected_output": "[0, 1]"}],
            concept_ids=["cs-var-loops"],
            visibility="public",
        )
        session.add(problem)
        await session.commit()
        await session.refresh(problem)
        return problem
