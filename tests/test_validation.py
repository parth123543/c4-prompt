"""Unit tests for Input Validation and Code Reviewer parsing."""

import pytest
from modules.prompt_engine import PromptEngine
from modules.code_reviewer import CodeReviewer


def test_empty_code_validation():
    engine = PromptEngine()
    is_valid, err = engine.validate_code_input("", "Task description")
    assert is_valid is False
    assert "empty" in err.lower()

    is_valid2, err2 = engine.validate_code_input("   \n\t  ", "Task")
    assert is_valid2 is False
    assert "empty" in err2.lower()


def test_short_code_validation():
    engine = PromptEngine()
    is_valid, err = engine.validate_code_input("x=1", "Task")
    assert is_valid is False
    assert "too short" in err.lower()


def test_random_text_validation():
    engine = PromptEngine()
    gibberish = "asdkjasd qwerty zxcvbnm poiuytrew mnbvcxz"
    is_valid, err = engine.validate_code_input(gibberish, "Task")
    assert is_valid is False
    assert "random text" in err.lower()


def test_valid_code_validation():
    engine = PromptEngine()
    valid_code = "def sum_nums(a, b):\n    return a + b\n"
    is_valid, err = engine.validate_code_input(valid_code, "Add two numbers")
    assert is_valid is True
    assert err == ""


def test_reviewer_parse_sections():
    reviewer = CodeReviewer()
    markdown_mock = (
        "### 1. Overall Assessment\nGreat start on this function!\n\n"
        "### 2. Bugs and Errors\n- **Error Name**: Missing Colon\n\n"
        "### 3. Coding Style Issues\n- Use 4 spaces for indentation.\n\n"
        "### 4. Progressive Hints\n"
        "- **Hint 1 (Conceptual Clue)**: Look at syntax.\n"
        "- **Hint 2 (Specific Guidance)**: Check line 1.\n"
        "- **Hint 3 (Strongest Clue)**: Add a colon at the end.\n\n"
        "### 5. Suggested Test Cases\nNormal: 5 -> 10\n\n"
        "### 6. What To Try Next\n1. Add colon.\n2. Re-run.\n"
    )

    parsed = reviewer.parse_sections(markdown_mock)
    assert "Great start" in parsed["assessment"]
    assert "Missing Colon" in parsed["bugs"]
    assert "4 spaces" in parsed["style"]
    assert "Look at syntax" in parsed["hint_1"]
    assert "Check line 1" in parsed["hint_2"]
    assert "Add a colon" in parsed["hint_3"]
    assert "Suggested Test Cases" not in parsed["test_cases"] or "5 -> 10" in parsed["test_cases"]
    assert "What To Try Next" not in parsed["next_steps"] or "Add colon" in parsed["next_steps"]
