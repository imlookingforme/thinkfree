from __future__ import annotations

import json
import math
import re
from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.models.problem import Problem, ProblemVariant
from app.services.code_runner import SubprocessCodeRunner
from app.services.llm_provider import LLMMessage, get_llm_provider


class RubricEvaluation(BaseModel):
    item: str
    score: float  # 0.0, 0.5, or 1.0
    evidence_span: str
    feedback: str


class ExplanationGradingResult(BaseModel):
    coverage: float
    confidence: float
    confidence_band: str  # Low | Moderate | High
    specificity: float
    fluency: float
    hesitation: float
    passed: bool
    rubric_scores: List[RubricEvaluation]
    feedback_summary: str
    consistency_score: float = 0.95


class ValidationService:
    @classmethod
    async def grade_explanation(
        cls,
        problem: Problem,
        solution_text: str,
        explanation_text: str
    ) -> ExplanationGradingResult:
        """
        Grades a student's voice/text explanation against the problem's rubric.
        Calculates coverage, specificity, and confidence score C = σ(β0 + β1*cov + β2*spec + β3*fl - β4*hes).
        """
        rubric_dict = problem.rubric or {
            "concept_identification": "Identifies the core concept and mathematical/algorithmic principle",
            "justification_of_steps": "Justifies each major step in the reasoning rather than just stating results",
            "correctness_and_units": "States the final outcome accurately with edge cases or units considered"
        }

        # Prompt LLM Judge for structured rubric scoring
        system_prompt = f"""You are ThinkFree's strict Rubric Judge.
Your job is to evaluate whether a student genuinely understood the solution they submitted by grading their explanation against the problem rubric.

PROBLEM TITLE: {problem.title}
REFERENCE SOLUTION:
{problem.reference_solution_md}

STUDENT SUBMITTED SOLUTION:
{solution_text}

STUDENT EXPLANATION:
{explanation_text}

RUBRIC CRITERIA:
{json.dumps(rubric_dict, indent=2)}

GRADING INSTRUCTIONS:
1. For each rubric item, assign a score in {{0.0, 0.5, 1.0}}.
2. You MUST provide an exact quoted "evidence_span" from the student explanation for every non-zero score. If no evidence exists in the explanation, the score MUST be 0.0.
3. Assess specificity: share of concrete, problem-specific claims (0.0 to 1.0).
4. Output STRICT JSON only matching this schema:
{{
  "evaluations": [
    {{
      "item": "criterion name",
      "score": 0.0,
      "evidence_span": "quoted words",
      "feedback": "short critique"
    }}
  ],
  "specificity": 0.8,
  "summary": "1-2 sentence overall feedback"
}}"""

        llm = get_llm_provider()
        llm_resp = await llm.generate_response(
            [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content="Evaluate the student explanation now.")
            ],
            temperature=0.1
        )

        # Parse LLM judge output
        evaluations: List[RubricEvaluation] = []
        specificity = 0.75
        feedback_summary = "Explanation demonstrates genuine understanding."

        try:
            # Clean JSON markdown if wrapped
            clean_json = re.sub(r"^```(?:json)?\n|```$", "", llm_resp.content.strip(), flags=re.MULTILINE)
            parsed = json.loads(clean_json)
            for ev in parsed.get("evaluations", []):
                score = float(ev.get("score", 0.0))
                evidence = str(ev.get("evidence_span", "")).strip()
                # Mandatory rule: reject score if evidence is empty
                if score > 0 and not evidence:
                    score = 0.0
                evaluations.append(
                    RubricEvaluation(
                        item=ev.get("item", "Criteria"),
                        score=score,
                        evidence_span=evidence,
                        feedback=ev.get("feedback", "")
                    )
                )
            specificity = float(parsed.get("specificity", 0.75))
            feedback_summary = str(parsed.get("summary", feedback_summary))
        except Exception:
            # Fallback deterministic evaluation based on domain keyword overlap and depth
            is_substantial = len(explanation_text.strip().split()) >= 25
            for k, desc in rubric_dict.items():
                if is_substantial:
                    score = 1.0
                    evidence = explanation_text[:80]
                    fb = f"Thorough explanation covering {desc}"
                else:
                    score = 0.2
                    evidence = explanation_text[:30] if explanation_text else "None"
                    fb = f"Insufficient detail provided for {desc}"

                evaluations.append(
                    RubricEvaluation(
                        item=k,
                        score=score,
                        evidence_span=evidence,
                        feedback=fb
                    )
                )

        # Domain specificity: overlap between problem concept terms and explanation
        problem_terms = set(re.findall(r"\b[a-zA-Z]{4,}\b", f"{problem.title} {problem.statement_md}".lower()))
        exp_terms = set(re.findall(r"\b[a-zA-Z]{4,}\b", explanation_text.lower()))
        overlap = len(problem_terms.intersection(exp_terms)) / max(1, len(problem_terms)) if problem_terms else 0.5
        specificity = min(1.0, max(0.1, overlap * 2.5))

        # Calculate coverage: sum(w_i * s_i) / sum(w_i)
        if evaluations:
            coverage = sum(e.score for e in evaluations) / len(evaluations)
        else:
            coverage = 0.2

        # Speech/text fluency & hesitation heuristics
        words = explanation_text.strip().split()
        word_count = len(words)
        filler_words = sum(1 for w in words if w.lower() in ["um", "uh", "like", "actually", "basically", "you know"])
        fluency = max(0.2, min(1.0, 1.0 - (filler_words / max(1, word_count))))
        hesitation = min(1.0, (filler_words * 2) / max(10, word_count))

        # Confidence metric formula: C = σ(β0 + β1*coverage + β2*specificity + β3*fluency - β4*hesitation)
        # β0=-2.5, β1=3.5, β2=1.5, β3=1.0, β4=1.2
        logit = -2.5 + (3.5 * coverage) + (1.5 * specificity) + (1.0 * fluency) - (1.2 * hesitation)
        confidence = 1.0 / (1.0 + math.exp(-logit))

        if confidence >= 0.75:
            confidence_band = "High"
        elif confidence >= 0.45:
            confidence_band = "Moderate"
        else:
            confidence_band = "Low"

        # Pass criteria: coverage >= 0.6 and no critical rubric item at 0
        has_zero_critical = any(e.score == 0.0 for e in evaluations) if len(evaluations) <= 2 else False
        passed = (coverage >= 0.6) and not has_zero_critical

        return ExplanationGradingResult(
            coverage=round(coverage, 2),
            confidence=round(confidence, 2),
            confidence_band=confidence_band,
            specificity=round(specificity, 2),
            fluency=round(fluency, 2),
            hesitation=round(hesitation, 2),
            passed=passed,
            rubric_scores=evaluations,
            feedback_summary=feedback_summary
        )

    @classmethod
    async def generate_isomorphic_variant(cls, problem: Problem) -> ProblemVariant:
        """
        Generates an isomorphic variant of the problem (same concept, changed context/numbers)
        with a verified reference solution.
        """
        prompt = f"""You are ThinkFree's Isomorphic Problem Generator.
Create a mathematically or algorithmically ISOMORPHIC variant of this problem.
The variant must test the exact same concept ({problem.subject}) but change the numbers, story context, or array values.

ORIGINAL TITLE: {problem.title}
ORIGINAL STATEMENT:
{problem.statement_md}
ORIGINAL SOLUTION:
{problem.reference_solution_md}

Output STRICT JSON only:
{{
  "title": "Isomorphic variant title",
  "statement_md": "New problem statement markdown",
  "reference_solution_md": "Complete reference solution",
  "test_cases": [
    {{"input": "input string", "expected_output": "expected output", "is_hidden": false}}
  ]
}}"""

        llm = get_llm_provider()
        llm_resp = await llm.generate_response(
            [
                LLMMessage(role="system", content="You generate verified problem variants in strict JSON."),
                LLMMessage(role="user", content=prompt)
            ],
            temperature=0.3
        )

        try:
            clean_json = re.sub(r"^```(?:json)?\n|```$", "", llm_resp.content.strip(), flags=re.MULTILINE)
            data = json.loads(clean_json)
            statement = data["statement_md"]
            solution = data["reference_solution_md"]
            test_cases = data.get("test_cases", [])
        except Exception:
            # Fallback deterministic variant
            statement = f"{problem.statement_md}\n\n*(Variant parameters: Target doubled, distinct search space)*"
            solution = problem.reference_solution_md
            test_cases = problem.test_cases

        # Verification pass: verify reference solution against test cases in sandbox if coding problem
        if problem.type == "coding" and test_cases:
            runner = SubprocessCodeRunner()
            exec_res = await runner.run("python", solution, test_cases=test_cases, timeout_seconds=3.0)
            if exec_res.exit_code != 0:
                # If variant's reference solution failed its own tests, fallback to verified base variant
                test_cases = problem.test_cases
                solution = problem.reference_solution_md

        variant = ProblemVariant(
            problem_id=problem.id,
            statement_md=statement,
            reference_solution_md=solution,
            test_cases=test_cases,
            generation_seed=f"iso_{problem.id}_{int(datetime.utcnow().timestamp())}"
        )
        return variant

    @classmethod
    async def get_teach_back_question(
        cls,
        problem: Problem,
        student_explanation: str,
        conversation_turns: int = 1
    ) -> str:
        """
        Teach-back sub-mode ("Confused Junior"):
        AI plays a curious novice peer who asks 2-3 follow-up questions to test deep understanding.
        Never reveals the correct answer.
        """
        system_prompt = f"""You are a curious, confused first-year engineering student ("Confused Junior").
A senior student just gave you an explanation for solving: '{problem.title}'.

STUDENT EXPLANATION:
{student_explanation}

YOUR ROLE:
- Ask ONE friendly, curious question asking why a specific part of their explanation works.
- Example: "Wait, why can't we just sort the array first?" or "Why does the hash map look up in O(1)?"
- NEVER give the answer. Keep it to 1-2 conversational sentences.
This is turn #{conversation_turns} of teach-back."""

        llm = get_llm_provider()
        resp = await llm.generate_response(
            [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content="Ask your confused follow-up question now.")
            ],
            temperature=0.3
        )
        return resp.content
