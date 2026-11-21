from __future__ import annotations

from datetime import datetime
from typing import Dict

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.problem import Problem
from app.models.session import Session, TutorMessage
from app.services.leak_guard import LeakGuard
from app.services.llm_provider import LLMMessage, get_llm_provider

RUNG_WEIGHTS: Dict[str, float] = {
    "guide": 0.15,
    "hint": 0.35,
    "help": 0.55,
    "critical_hint": 0.80,
}

HINT_BUDGET_DEFAULT: int = 6


class TutorService:
    @staticmethod
    def get_system_prompt(problem: Problem, rung: str, stricter: bool = False) -> str:
        prompt = f"""You are ThinkFree's Socratic AI Tutor.
Your goal is to guide the student to think independently, discover principles, and solve the problem themselves.

PROBLEM INFORMATION:
Title: {problem.title}
Subject: {problem.subject}
Problem Statement:
{problem.statement_md}

ACTIVE TUTOR RUNG: {rung.upper()}
Weight: {RUNG_WEIGHTS.get(rung, 0.25)}

STRICT PEDAGOGICAL RULES (NEVER VIOLATE):
1. NEVER output the final answer, a full solution, or code that passes the problem's tests.
2. If the user asks for the answer or asks you to write the full code, kindly refuse and offer a thought-provoking hint instead.
3. Keep your response concise (2-4 sentences or a short bulleted scaffold), ending with a question prompting the student to take the next step.
"""
        if rung == "guide":
            prompt += "\nBEHAVIOR: Ask a high-level Socratic question about the underlying concept or approach. Do not give any implementation details."
        elif rung == "hint":
            prompt += "\nBEHAVIOR: Point to the relevant data structure, invariant, or mathematical rule without executing it. Ask how it could apply."
        elif rung == "help":
            prompt += "\nBEHAVIOR: Explain the concept and illustrate with a COMPLETELY DIFFERENT worked example from a different domain. Do NOT solve this problem."
        elif rung == "critical_hint":
            prompt += "\nBEHAVIOR: Show only the NEXT SINGLE atomic step (e.g., initial condition or loop setup), never the full algorithm."

        if stricter:
            prompt += "\n\nCRITICAL WARNING: The previous response was blocked by the safety leak-guard for being too close to the solution. Be EXTREMELY minimal. Ask only a clarifying question."

        return prompt

    @classmethod
    async def generate_tutor_reply(
        cls,
        db: AsyncSession,
        session_id: str,
        student_id: str,
        user_message: str,
        rung: str = "guide",
        is_elaborate: bool = False,
        hint_budget: int = HINT_BUDGET_DEFAULT,
    ) -> TutorMessage:
        session = await db.get(Session, session_id)
        if not session or session.student_id != student_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        # Must be in guided mode (unlocked)
        if session.state != "guided":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tutor is only accessible in 'guided' mode. Current state: '{session.state}'",
            )

        # Check hint budget
        result = await db.execute(
            select(TutorMessage).where(
                TutorMessage.session_id == session_id, TutorMessage.role == "tutor"
            )
        )
        previous_tutor_messages = result.scalars().all()
        if len(previous_tutor_messages) >= hint_budget:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hint budget exhausted ({hint_budget}/{hint_budget} hints used). Please proceed to the validation phase.",
            )

        problem = await db.get(Problem, session.problem_id)
        if not problem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

        # Record student prompt
        student_msg = TutorMessage(
            session_id=session.id,
            role="student",
            rung=rung,
            content=user_message,
            ts=datetime.utcnow(),
        )
        db.add(student_msg)

        # Prepare messages for LLM
        system_prompt = cls.get_system_prompt(problem, rung, stricter=False)
        llm_messages = [LLMMessage(role="system", content=system_prompt)]

        # Context: Student's current solution / code attempt
        if session.current_solution:
            llm_messages.append(
                LLMMessage(
                    role="system",
                    content=f"Student's current working solution:\n```\n{session.current_solution[:1500]}\n```",
                )
            )

        # Conversation history (last 6 messages)
        recent_history = previous_tutor_messages[-6:]
        for prev in recent_history:
            llm_messages.append(LLMMessage(role=prev.role, content=prev.content))

        # Add current user prompt
        llm_messages.append(LLMMessage(role="user", content=user_message))

        llm_provider = get_llm_provider()
        leak_guard = LeakGuard()

        # First generation pass
        llm_resp = await llm_provider.generate_response(llm_messages, temperature=0.2)
        leak_check = await leak_guard.check(llm_resp.content, problem)

        final_content = llm_resp.content

        # Second line of defense: Retry with stricter prompt if leak detected
        if not leak_check.passed:
            stricter_system = cls.get_system_prompt(problem, rung, stricter=True)
            llm_messages[0] = LLMMessage(role="system", content=stricter_system)

            retry_resp = await llm_provider.generate_response(llm_messages, temperature=0.1)
            retry_leak = await leak_guard.check(retry_resp.content, problem)

            if retry_leak.passed:
                final_content = retry_resp.content
                leak_check = retry_leak
            else:
                # Fallback to safe template question
                final_content = LeakGuard.get_safe_fallback_question(problem, rung)
                leak_check.details += " -> Fallback question used."

        # Update session help cost
        weight = RUNG_WEIGHTS.get(rung, 0.25)
        session.help_cost += weight

        # Save tutor message with leak_check metadata
        tutor_msg = TutorMessage(
            session_id=session.id,
            role="tutor",
            rung=rung,
            content=final_content,
            leak_check=leak_check.model_dump(),
            ts=datetime.utcnow(),
        )
        db.add(tutor_msg)
        await db.commit()
        await db.refresh(tutor_msg)

        return tutor_msg
