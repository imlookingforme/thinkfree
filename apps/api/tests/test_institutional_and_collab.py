from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings
from app.models.user import Course, Enrollment, User
from app.services.auth_service import AuthService
from app.services.badge_service import BadgeService
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_ed25519_badge_signature_and_tamper_detection():
    """
    Feature 11: Cryptographic badge verification test.
    - Valid signature passes verification.
    - Tampered payload (e.g. altering ITS score) fails verification.
    """
    payload = BadgeService.create_badge_payload(
        student_id="student_123",
        kind="independent_foundations",
        title="Foundations of Data Structures — Independent Achiever",
        institution_name="BITS Pilani",
        its_score=88.5,
        adr_score=0.15,
        self_solves_count=30
    )
    sig = BadgeService.sign_payload(payload)

    # 1. Honest verification
    res_valid = BadgeService.verify_badge(badge_id="badge_1", payload=payload, signature_str=sig)
    assert res_valid.is_valid
    assert res_valid.title == "Foundations of Data Structures — Independent Achiever"
    assert res_valid.error is None

    # 2. Tampered payload verification
    tampered_payload = dict(payload)
    tampered_payload["criteria"] = dict(payload["criteria"])
    tampered_payload["criteria"]["achieved_its"] = 99.9  # Fraudulent elevation

    res_invalid = BadgeService.verify_badge(badge_id="badge_1", payload=tampered_payload, signature_str=sig)
    assert not res_invalid.is_valid
    assert "failed" in (res_invalid.error or "").lower()


@pytest.mark.asyncio
async def test_institutional_professor_portal_and_lti_api(client: AsyncClient):
    """
    Feature 10: Professor cohort view, assignment creation, badge issuance, and LTI 1.3 launch.
    """
    async with TestSessionLocal() as db:
        # Create Professor
        prof = User(
            email="prof_phase5@test.com",
            name="Prof Sharma",
            password_hash="mock",
            role="professor"
        )
        # Create Student
        student = User(
            email="student_phase5@test.com",
            name="Student Pilani",
            password_hash="mock",
            role="student"
        )
        db.add_all([prof, student])
        await db.commit()
        await db.refresh(prof)
        await db.refresh(student)

        course = Course(
            name="CS F211 Data Structures",
            professor_id=prof.id
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)

        enr = Enrollment(course_id=course.id, student_id=student.id)
        db.add(enr)
        await db.commit()

        prof_id = prof.id
        student_id = student.id
        course_id = course.id

    prof_token = AuthService.create_access_token({"sub": prof_id, "role": "professor"})
    client.cookies.set(settings.SESSION_COOKIE_NAME, prof_token)

    # 1. Test Cohort Analytics
    cohort_res = await client.get(f"/api/v1/institutional/cohort/{course_id}")
    assert cohort_res.status_code == 200
    cohort_data = cohort_res.json()
    assert cohort_data["total_students"] == 1
    assert "cohort_mean_its" in cohort_data
    assert "reliance_distribution" in cohort_data

    # 2. Test Assignment Creation with Policy
    asg_res = await client.post(
        "/api/v1/institutional/assignments",
        json={
            "course_id": course_id,
            "title": "Assignment 1: Linked Lists",
            "problem_ids": ["prob_1", "prob_2"],
            "ai_policy": "locked",
            "due_days_ahead": 7,
            "validation_required": True
        }
    )
    assert asg_res.status_code == 200
    assert asg_res.json()["ai_policy"] == "locked"

    # 3. Test Badge Issuance
    badge_res = await client.post(
        "/api/v1/institutional/badges/issue",
        json={
            "student_id": student_id,
            "kind": "independent_achiever",
            "title": "Data Structures Independent Achiever"
        }
    )
    assert badge_res.status_code == 200
    b_data = badge_res.json()
    assert "signature" in b_data
    assert "verify_url" in b_data
    badge_id = b_data["id"]

    # 4. Test Public Zero-Auth Verification
    client.cookies.clear()  # Clear cookies to simulate anonymous public visitor
    pub_res = await client.get(f"/api/v1/institutional/badges/verify/{badge_id}")
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["is_valid"]
    assert pub_data["title"] == "Data Structures Independent Achiever"

    # 5. Test LTI 1.3 Advantage Launch
    lti_res = await client.post("/api/v1/institutional/lti/launch")
    assert lti_res.status_code == 200
    assert lti_res.json()["protocol"] == "LTI-1.3-Advantage"


@pytest.mark.asyncio
async def test_collaboration_and_privacy_api(client: AsyncClient):
    """
    Features 9 & 12: Projects, task attribution, external AI self-report, and DPDP Act 2023 export.
    """
    async with TestSessionLocal() as db:
        user = User(
            email="collab_student@test.com",
            name="Collab Student",
            password_hash="mock",
            role="student"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        user_id = user.id

    token = AuthService.create_access_token({"sub": user_id, "role": "student"})
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    # 1. Create Linear-Style Project
    proj_res = await client.post(
        "/api/v1/collab/projects",
        json={
            "name": "Course Capstone: Compiler Design",
            "description": "Lexer and Parser implementation",
            "ai_policy": "guided"
        }
    )
    assert proj_res.status_code == 200
    proj_id = proj_res.json()["id"]

    # 2. Create Task with AI Policy
    task_res = await client.post(
        f"/api/v1/collab/projects/{proj_id}/tasks",
        json={
            "project_id": proj_id,
            "title": "Implement Recursive Descent AST",
            "ai_policy": "locked"
        }
    )
    assert task_res.status_code == 200
    task_id = task_res.json()["id"]

    # 3. Record Task Contribution Audit Event
    audit_res = await client.post(
        f"/api/v1/collab/tasks/{task_id}/event",
        json={"action": "self_solve", "details": {"lines_committed": 140}}
    )
    assert audit_res.status_code == 200
    assert audit_res.json()["status"] == "audit_event_recorded"

    # 4. External AI Self-Reporting (Feature 12)
    ext_res = await client.post(
        "/api/v1/collab/external-ai/report",
        json={
            "tool_name": "ChatGPT",
            "purpose": "Syntax syntax lookup for python AST module",
            "minutes_used": 15
        }
    )
    assert ext_res.status_code == 200
    assert "self_awareness_boost" in ext_res.json()

    # 5. DPDP Privacy Export (Feature 12)
    priv_res = await client.get("/api/v1/collab/privacy/export")
    assert priv_res.status_code == 200
    priv_data = priv_res.json()
    assert "dpdp_compliance" in priv_data
    assert priv_data["dpdp_compliance"]["keylogging"] == "None (aggregated 5s telemetry only)"
