import pytest

from app.services.code_runner import SubprocessCodeRunner


@pytest.mark.asyncio
async def test_code_runner_python_success():
    runner = SubprocessCodeRunner()
    code = "print('Hello ThinkFree')"
    res = await runner.run("python", code)
    assert res.exit_code == 0
    assert res.stdout.strip() == "Hello ThinkFree"
    assert res.timed_out is False


@pytest.mark.asyncio
async def test_code_runner_python_with_stdin():
    runner = SubprocessCodeRunner()
    code = "name = input()\nprint(f'Hello {name}')"
    res = await runner.run("python", code, stdin="World")
    assert res.exit_code == 0
    assert res.stdout.strip() == "Hello World"


@pytest.mark.asyncio
async def test_code_runner_test_cases():
    runner = SubprocessCodeRunner()
    code = """
import sys

def solve():
    val = int(sys.stdin.read().strip())
    print(val * 2)

solve()
"""
    test_cases = [
        {"input": "2", "expected_output": "4", "is_hidden": False},
        {"input": "5", "expected_output": "10", "is_hidden": True},
        {"input": "3", "expected_output": "7", "is_hidden": False},  # Intentionally failing
    ]
    res = await runner.run("python", code, test_cases=test_cases)
    assert res.exit_code == 1  # Not all passed
    assert len(res.test_results) == 3
    assert res.test_results[0]["passed"] is True
    assert res.test_results[1]["passed"] is True
    assert res.test_results[2]["passed"] is False


@pytest.mark.asyncio
async def test_code_runner_timeout():
    runner = SubprocessCodeRunner()
    code = "import time\ntime.sleep(10)"
    res = await runner.run("python", code, timeout_seconds=0.5)
    assert res.timed_out is True
    assert res.exit_code == -1
