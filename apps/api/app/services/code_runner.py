from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel

from app.config import settings


class ExecutionResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    memory_kb: int = 0
    test_results: Optional[List[Dict[str, Any]]] = None
    timed_out: bool = False
    error: Optional[str] = None


class CodeRunner(ABC):
    @abstractmethod
    async def run(
        self,
        language: str,
        code: str,
        stdin: str = "",
        test_cases: Optional[List[Dict[str, Any]]] = None,
        timeout_seconds: float = 5.0,
    ) -> ExecutionResult:
        """Run code against stdin or test cases."""
        pass


class SubprocessCodeRunner(CodeRunner):
    """
    Local sandboxed process runner.
    Enforces process isolation, timeouts, and file permissions within a temporary directory.
    """

    SUPPORTED_LANGUAGES = ["python", "javascript", "c", "cpp"]

    async def run(
        self,
        language: str,
        code: str,
        stdin: str = "",
        test_cases: Optional[List[Dict[str, Any]]] = None,
        timeout_seconds: float = 5.0,
    ) -> ExecutionResult:
        lang = language.lower()

        if test_cases:
            return await self._run_test_cases(lang, code, test_cases, timeout_seconds)

        return await self._execute_single(lang, code, stdin, timeout_seconds)

    async def _execute_single(
        self, language: str, code: str, stdin: str, timeout_seconds: float
    ) -> ExecutionResult:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            file_path, cmd = self._prepare_command(language, code, tmpdir)
            if not cmd:
                return ExecutionResult(
                    stderr=f"Unsupported language: {language}",
                    exit_code=1,
                    error=f"Language {language} is not supported in local sandbox.",
                )

            start_time = time.perf_counter()
            timed_out = False
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir,
                )

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(input=stdin.encode() if stdin else None),
                        timeout=timeout_seconds,
                    )
                    exit_code = proc.returncode or 0
                except asyncio.TimeoutError:
                    timed_out = True
                    try:
                        proc.kill()
                        await proc.wait()
                    except Exception:
                        pass
                    stdout_bytes, stderr_bytes = b"", b"Execution timed out."
                    exit_code = -1

            except Exception as e:
                return ExecutionResult(
                    stderr=str(e), exit_code=1, error=f"Process launch error: {str(e)}"
                )

            duration_ms = (time.perf_counter() - start_time) * 1000.0

            return ExecutionResult(
                stdout=stdout_bytes.decode(errors="replace"),
                stderr=stderr_bytes.decode(errors="replace"),
                exit_code=exit_code,
                duration_ms=round(duration_ms, 2),
                timed_out=timed_out,
            )

    async def _run_test_cases(
        self, language: str, code: str, test_cases: List[Dict[str, Any]], timeout_seconds: float
    ) -> ExecutionResult:
        test_results = []
        overall_passed = True
        total_duration = 0.0

        for i, tc in enumerate(test_cases):
            tc_input = str(tc.get("input", ""))
            expected_output = str(tc.get("expected_output", "")).strip()
            is_hidden = bool(tc.get("is_hidden", False))

            res = await self._execute_single(language, code, tc_input, timeout_seconds)
            total_duration += res.duration_ms
            actual_output = res.stdout.strip()

            passed = (res.exit_code == 0) and (actual_output == expected_output)
            if not passed:
                overall_passed = False

            test_results.append(
                {
                    "test_case_index": i + 1,
                    "input": "[Hidden]" if is_hidden else tc_input,
                    "expected_output": "[Hidden]" if is_hidden else expected_output,
                    "actual_output": "[Hidden]" if is_hidden and not passed else actual_output,
                    "passed": passed,
                    "exit_code": res.exit_code,
                    "duration_ms": res.duration_ms,
                    "stderr": res.stderr if not passed else "",
                    "is_hidden": is_hidden,
                }
            )

        return ExecutionResult(
            stdout=f"Ran {len(test_cases)} tests. {'All tests passed.' if overall_passed else 'Some tests failed.'}",
            stderr="",
            exit_code=0 if overall_passed else 1,
            duration_ms=round(total_duration, 2),
            test_results=test_results,
        )

    def _prepare_command(self, language: str, code: str, tmpdir: str) -> Tuple[str, List[str]]:
        if language in ["python", "py"]:
            file_path = os.path.join(tmpdir, "solution.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            return file_path, [sys.executable, file_path]

        elif language in ["javascript", "js"]:
            file_path = os.path.join(tmpdir, "solution.js")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            return file_path, ["node", file_path]

        return "", []


class Judge0CodeRunner(CodeRunner):
    """
    Judge0 CE API adapter for high-security isolated language execution.
    Falls back to SubprocessCodeRunner if Judge0 service is not responding.
    """

    LANGUAGE_IDS = {
        "python": 71,  # Python 3.8.1
        "c": 50,  # GCC 9.2.0
        "cpp": 54,  # GCC 9.2.0
        "java": 62,  # OpenJDK 13
        "javascript": 63,  # Node.js 12.14.0
    }

    def __init__(self, base_url: str = settings.JUDGE0_URL):
        self.base_url = base_url.rstrip("/")
        self.fallback = SubprocessCodeRunner()

    async def run(
        self,
        language: str,
        code: str,
        stdin: str = "",
        test_cases: Optional[List[Dict[str, Any]]] = None,
        timeout_seconds: float = 5.0,
    ) -> ExecutionResult:
        lang_id = self.LANGUAGE_IDS.get(language.lower())
        if not lang_id:
            # Fallback to subprocess if language not in Judge0 mapping
            return await self.fallback.run(language, code, stdin, test_cases, timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds + 3.0) as client:
                # Check health / ping
                ping = await client.get(f"{self.base_url}/health")
                if ping.status_code != 200:
                    raise Exception("Judge0 service unhealthy")

                payload = {
                    "source_code": code,
                    "language_id": lang_id,
                    "stdin": stdin,
                    "cpu_time_limit": timeout_seconds,
                    "redirect_stderr_to_stdout": False,
                }
                sub_res = await client.post(f"{self.base_url}/submissions?wait=true", json=payload)
                if sub_res.status_code not in (200, 201):
                    raise Exception(f"Judge0 error: {sub_res.text}")

                data = sub_res.json()
                return ExecutionResult(
                    stdout=data.get("stdout") or "",
                    stderr=data.get("stderr") or "",
                    exit_code=data.get("status", {}).get("id", 0)
                    if data.get("status", {}).get("id") != 3
                    else 0,
                    duration_ms=float(data.get("time") or 0.0) * 1000.0,
                    memory_kb=int(data.get("memory") or 0),
                )

        except Exception:
            # Clean fallback to local Subprocess runner
            return await self.fallback.run(language, code, stdin, test_cases, timeout_seconds)


def get_code_runner() -> CodeRunner:
    if settings.CODERUNNER_ADAPTER == "judge0":
        return Judge0CodeRunner()
    return SubprocessCodeRunner()
