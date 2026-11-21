"""Unit tests for Provider Fallbacks, Demo Modes, and Test Manager."""

import pytest
from modules.openai_provider import OpenAIProvider
from modules.claude_provider import ClaudeProvider
from modules.gemini_provider import GeminiProvider
from modules.code_reviewer import CodeReviewer
from modules.test_manager import TestManager


def test_openai_unconfigured_demo_fallback():
    provider = OpenAIProvider(api_key="")
    assert provider.is_configured() is False

    res = provider.review_code(
        system_prompt="Test sys",
        user_prompt="Test user",
        demo_fallback=True,
        context={"language": "Python", "code": "def add(a, b):\n return a - b", "task_description": "Add"}
    )
    assert res["is_demo"] is True
    assert "SIMULATED DEMO MODE" in res["content"]
    assert "Overall Assessment" in res["content"]
    assert "Progressive Hints" in res["content"]


def test_claude_unconfigured_demo_fallback():
    provider = ClaudeProvider(api_key="")
    assert provider.is_configured() is False

    res = provider.review_code(
        system_prompt="Test sys",
        user_prompt="Test user",
        demo_fallback=True,
        context={"language": "Python", "code": "def check(x):\n if x > 0\n  return True", "task_description": "Check"}
    )
    assert res["is_demo"] is True
    assert "SIMULATED DEMO MODE" in res["content"]
    assert "Missing Syntax Delimiter" in res["content"] or "Bugs and Errors" in res["content"]


def test_gemini_unconfigured_demo_fallback():
    provider = GeminiProvider(api_key="")
    assert provider.is_configured() is False

    res = provider.review_code(
        system_prompt="Test sys",
        user_prompt="Test user",
        demo_fallback=True,
        context={"language": "Python", "code": "def f(n):\n result = 0\n for i in range(1, n): result *= i", "task_description": "Fact"}
    )
    assert res["is_demo"] is True
    assert "SIMULATED DEMO MODE" in res["content"]
    assert "Multiplicative Identity" in res["content"] or "Bugs and Errors" in res["content"]


def test_code_reviewer_pipeline():
    reviewer = CodeReviewer()
    # Test review dispatch in demo fallback
    res = reviewer.review(
        language="Python",
        task_description="Sum 1 to n",
        code="def sum_to_n(n):\n    total = 0\n    for i in range(1, n):\n        total += i\n    return total",
        provider_name="Gemini",
        prompt_version="v3"
    )
    assert res["success"] is True
    assert res["compliance"]["compliant"] is True
    assert res["parsed_sections"]["assessment"] != ""
    assert res["parsed_sections"]["hints"] != ""


def test_test_manager_cases_loaded():
    mgr = TestManager()
    cases = mgr.get_test_cases()
    assert len(cases) >= 12
    test_ids = [c["test_id"] for c in cases]
    for expected_id in ["TC01", "TC02", "TC03", "TC04", "TC05", "TC06", "TC07", "TC08", "TC09", "TC10", "TC11", "TC12"]:
        assert expected_id in test_ids


def test_test_manager_run_tc10_empty_code():
    reviewer = CodeReviewer()
    mgr = TestManager()
    run_res = mgr.run_test("TC10", reviewer, provider_name="Gemini")
    assert run_res["evaluation"]["pass_fail"] == "PASS"
    assert "Validation" in run_res["evaluation"]["actual_category_detected"]
