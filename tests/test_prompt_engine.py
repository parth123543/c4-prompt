"""Unit tests for Prompt Engine module."""

import pytest
from modules.prompt_engine import PromptEngine


def test_prompt_engine_initialization():
    engine = PromptEngine()
    assert engine.prompts_dir is not None


def test_get_system_prompt_versions():
    engine = PromptEngine()
    v1_prompt = engine.get_system_prompt("v1")
    v2_prompt = engine.get_system_prompt("v2")
    v3_prompt = engine.get_system_prompt("v3")
    final_prompt = engine.get_system_prompt("final")

    # V1 check
    assert "AI code reviewer" in v1_prompt or "review" in v1_prompt.lower()

    # V2 check - role + negative constraints
    assert "C4" in v2_prompt
    assert "NEVER provide" in v2_prompt or "never provide" in v2_prompt.lower()

    # V3 check - 6 structured sections + 9 constraints
    assert "Overall Assessment" in v3_prompt
    assert "Bugs and Errors" in v3_prompt
    assert "Coding Style Issues" in v3_prompt
    assert "Progressive Hints" in v3_prompt
    assert "Suggested Test Cases" in v3_prompt
    assert "What To Try Next" in v3_prompt

    # Final prompt should match V3
    assert "Progressive Hints" in final_prompt


def test_build_user_prompt():
    engine = PromptEngine()
    user_p = engine.build_user_prompt(
        language="Python",
        task_description="Compute sum of numbers 1 to n",
        student_code="def sum(n): return n"
    )

    assert "STUDENT PROGRAMMING LANGUAGE: Python" in user_p
    assert "Compute sum of numbers 1 to n" in user_p
    assert "def sum(n): return n" in user_p
    assert "Do NOT output the complete corrected program" in user_p


def test_solution_leakage_detector():
    engine = PromptEngine()
    student_code = "def add(a, b):\n    return a - b\n"

    # Compliant response with hints only
    compliant_resp = (
        "### 1. Overall Assessment\nGood effort.\n"
        "### 4. Progressive Hints\nHint 1: Check your operator.\n"
    )
    audit1 = engine.check_solution_leakage(compliant_resp, student_code)
    assert audit1["compliant"] is True
    assert audit1["leakage_detected"] is False

    # Leaking response with complete replacement function
    leaking_resp = (
        "Here is the complete corrected code:\n"
        "```python\n"
        "def add(a, b):\n"
        "    return a + b\n"
        "```\n"
    )
    audit2 = engine.check_solution_leakage(leaking_resp, student_code)
    assert audit2["compliant"] is False
    assert audit2["leakage_detected"] is True
