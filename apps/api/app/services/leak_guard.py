from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.problem import Problem
from app.services.code_runner import SubprocessCodeRunner


class LeakCheckResult(BaseModel):
    passed: bool
    method: str  # numeric_match | code_test_pass | solution_similarity | safe
    score: float = 0.0
    details: str = ""
    sanitized_response: Optional[str] = None


class LeakGuard:
    """
    Mandatory second line of defense.
    Verifies that generated tutor responses do NOT disclose final answers,
    full reference solutions, or code that passes the problem's test cases.
    """

    def __init__(self):
        self.code_runner = SubprocessCodeRunner()

    async def check(self, candidate_response: str, problem: Problem) -> LeakCheckResult:
        prob_type = problem.type.lower()

        # 1. Numeric / Short Answer normalized match check
        if prob_type == "numeric":
            numeric_res = self._check_numeric_leak(
                candidate_response, problem.reference_solution_md
            )
            if not numeric_res.passed:
                return numeric_res

        # 2. Code Extraction & Sandbox Execution check
        if prob_type == "coding" and problem.test_cases:
            code_res = await self._check_code_leak(candidate_response, problem.test_cases)
            if not code_res.passed:
                return code_res

        # 3. Direct Reference Solution Substring / Overlap check
        text_res = self._check_text_solution_leak(candidate_response, problem.reference_solution_md)
        if not text_res.passed:
            return text_res

        return LeakCheckResult(
            passed=True, method="safe", score=0.0, details="Passed all leak guard inspections."
        )

    def _check_numeric_leak(self, text: str, ref_solution: str) -> LeakCheckResult:
        # Extract numbers from reference solution (especially in 'Result = X' or final line)
        ref_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", ref_solution))
        if not ref_numbers:
            return LeakCheckResult(passed=True, method="numeric_match")

        # Check if the final answer number is directly stated as the answer in response
        for num in ref_numbers:
            # Pattern: "is 15", "= 15", "answer is 15", "result: 15"
            pattern = rf"(?:answer\s*(?:is|=|:)?\s*|result\s*(?:is|=|:)?\s*|=\s*){re.escape(num)}\b"
            if re.search(pattern, text, re.IGNORECASE):
                return LeakCheckResult(
                    passed=False,
                    method="numeric_match",
                    score=1.0,
                    details=f"Response leaked explicit numeric solution: {num}",
                )

        return LeakCheckResult(passed=True, method="numeric_match", score=0.0)

    async def _check_code_leak(
        self, candidate_text: str, test_cases: List[Dict[str, Any]]
    ) -> LeakCheckResult:
        # Extract code blocks from Markdown
        code_blocks = re.findall(r"```(?:python|py)?\n(.*?)```", candidate_text, re.DOTALL)
        if not code_blocks:
            return LeakCheckResult(passed=True, method="code_test_pass")

        for block in code_blocks:
            clean_code = block.strip()
            # If code is too short (just a fragment/header), ignore
            if len(clean_code.splitlines()) < 3:
                continue

            # Run code block against problem test cases in sandbox
            res = await self.code_runner.run(
                language="python", code=clean_code, test_cases=test_cases, timeout_seconds=3.0
            )

            if res.test_results:
                total_tests = len(res.test_results)
                passed_tests = sum(1 for t in res.test_results if t.get("passed"))
                pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0

                # BLOCK if pass rate >= 0.8
                if pass_rate >= 0.8:
                    return LeakCheckResult(
                        passed=False,
                        method="code_test_pass",
                        score=pass_rate,
                        details=f"Extracted code passed {passed_tests}/{total_tests} test cases ({int(pass_rate * 100)}% >= 80%). Leaked passing solution blocked.",
                    )

        return LeakCheckResult(passed=True, method="code_test_pass", score=0.0)

    def _check_text_solution_leak(self, text: str, ref_solution: str) -> LeakCheckResult:
        clean_text = " ".join(text.lower().split())
        clean_ref = " ".join(ref_solution.lower().split())

        # If more than 40 consecutive characters of reference solution appear verbatim in tutor output
        if len(clean_ref) > 50:
            for i in range(0, len(clean_ref) - 50, 20):
                chunk = clean_ref[i : i + 45]
                if chunk in clean_text:
                    return LeakCheckResult(
                        passed=False,
                        method="solution_similarity",
                        score=0.9,
                        details="Detected verbatim excerpt from reference solution.",
                    )

        # Direct answer giveaway phrases
        giveaway_patterns = [
            r"here is the (?:complete|full|final) (?:solution|code|answer)",
            r"the complete answer is\s*:",
            r"here is the answer\s*:",
        ]
        for pat in giveaway_patterns:
            if re.search(pat, text, re.IGNORECASE):
                return LeakCheckResult(
                    passed=False,
                    method="solution_similarity",
                    score=0.95,
                    details="Response contains explicit solution giveaway phrasing.",
                )

        return LeakCheckResult(passed=True, method="solution_similarity", score=0.0)

    @staticmethod
    def get_safe_fallback_question(problem: Problem, rung: str) -> str:
        """Safe fallback question returned when generation fails leak check twice."""
        if rung == "guide":
            return f"Let's step back: what fundamental principles or data structures from {problem.subject} apply to '{problem.title}'?"
        elif rung == "hint":
            return "Consider what partial information or invariant remains constant after each step of your proposed algorithm."
        elif rung == "help":
            return "Think about solving a smaller subproblem of size N=2. What operations would you perform by hand?"
        return (
            "What is the very first hypothesis you can test using the code sandbox or a test input?"
        )
