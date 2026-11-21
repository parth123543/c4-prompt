"""Simulated Demo Response Generator for C4 Code Review Assistant.

Generates structured mentor feedback adhering strictly to C4 constraints
when API keys are not supplied. Clearly labeled as Demo / Sample Mode.
"""

from __future__ import annotations
import re
from typing import Dict, Any


def generate_demo_review(
    provider_name: str,
    language: str,
    task_description: str,
    code: str,
    prompt_version: str = "v3"
) -> str:
    """Generates a realistic, pedagogical review strictly complying with C4 constraints.

    Clearly labeled as simulated output so the user is never misled.
    """
    lang_lower = (language or "python").lower()
    code_text = code or ""

    # Detect common student scenarios
    has_zero_div = "/" in code_text and ("len(" in code_text or "0" in code_text or "qty" in code_text)
    has_missing_colon = lang_lower == "python" and any(
        line.strip().startswith(("def ", "if ", "for ", "while ", "elif ", "else:")) and not line.strip().endswith(":")
        for line in code_text.splitlines() if line.strip() and not line.strip().startswith("#")
    )
    has_indentation = lang_lower == "python" and bool(
        re.search(r"^(?:for|def|if|while)\s+.*:\s*\n[a-zA-Z]", code_text, re.MULTILINE)
    )
    has_factorial_zero = "result = 0" in code_text and ("factorial" in code_text or "*" in code_text)
    has_off_by_one = "range(1, n)" in code_text or "range(0, len(" in code_text
    has_poor_vars = any(v in code_text for v in ["def f(", " x = ", " y = ", " z = ", " a = "])
    is_valid_simple = "def add(" in code_text or ("return a + b" in code_text)
    has_empty_list_risk = "numbers[0]" in code_text or "scores[0]" in code_text

    demo_banner = (
        "> ⚠️ **[SIMULATED DEMO MODE - OFFLINE EVALUATION]**\n"
        f"> *Provider Simulated: **{provider_name}** | Prompt Version: **{prompt_version.upper()}**.*\n"
        "> *To execute live AI reviews against actual cloud LLM endpoints, enter your API key in `.env` or the sidebar.*"
    )

    if prompt_version == "v1":
        # Baseline prompt - standard AI often dumps direct fixes
        return (
            f"{demo_banner}\n\n"
            f"### Code Review Analysis ({provider_name})\n\n"
            f"Here is an analysis of your {language} code:\n"
            f"- Your logic has an issue where the output will not match requirements.\n"
            f"- Line inspection indicates a syntax or runtime flaw.\n\n"
            f"**Suggested Fix:**\n"
            f"In V1 Baseline mode, typical unconstrained AI models often directly reveal corrected code:\n"
            f"```python\n"
            f"# Notice how baseline prompts fail pedagogical goals by writing code for the student:\n"
            f"# (In V2 and V3, C4 strictly forbids this code dump!)\n"
            f"```\n"
        )

    if prompt_version == "v2":
        # Improved - persona + negative constraints, but unstructured
        return (
            f"{demo_banner}\n\n"
            f"Hello! I am C4, your programming mentor. Let's look at your {language} program together.\n\n"
            f"First off, great job making an effort to solve this! As your mentor, I will not write the code for you, "
            f"because finding and fixing bugs yourself is where true programming confidence comes from.\n\n"
            f"**Observations:**\n"
            f"When I look at your code, I notice that the computer is trying to follow instructions that aren't quite complete. "
            f"Think carefully about what happens when your code runs line-by-line.\n"
            f"What value does your accumulator variable start with? How does the loop stop condition behave?\n\n"
            f"Try tracing your code on paper with a small sample input like `3` and watch what each variable holds!"
        )

    # V3 / Final - Full 6-Section Structured Pedagogical Output
    if has_missing_colon:
        bug_name = "Missing Syntax Delimiter (Colon ':')"
        bug_category = "Syntax Error"
        bug_location = "Header line of function definition or conditional statement"
        bug_severity = "Critical - prevents program from running"
        bug_explanation = (
            "In Python, statements that introduce a new code block (such as `def`, `if`, `for`, and `while`) "
            "must end with a colon `:`. The colon tells Python: 'Pay attention, an indented block of instructions follows!' "
            "Without it, Python's parser stops immediately before running any code."
        )
        hint1 = "Take a close look at the punctuation at the end of the line where you declared your function or condition."
        hint2 = "In English, a colon introduces a list or explanation. In Python, which character signals the start of a code block?"
        hint3 = "Check the very last character before you pressed Enter on the `def` or `if` line. Is there a `:` there?"
    elif has_factorial_zero:
        bug_name = "Multiplicative Identity Initialized to Zero"
        bug_category = "Logic Error"
        bug_location = "Initialization line (e.g., `result = 0`)"
        bug_severity = "Major - produces 0 for all factorial calculations"
        bug_explanation = (
            "In mathematics and computer science, 0 is the additive identity (anything + 0 = anything), but "
            "1 is the multiplicative identity. When you multiply anything by 0, the result is always 0. "
            "Because your loop repeatedly multiplies `result * i`, starting at 0 ensures the product remains 0 indefinitely."
        )
        hint1 = "Think about the difference between adding up a running total versus multiplying a running product."
        hint2 = "If you start with 0 candies and multiply by 2, how many candies do you have? What starting number preserves multiplication?"
        hint3 = "Look at the starting assignment for your accumulator variable. What number should you multiply by on the very first turn?"
    elif has_off_by_one:
        bug_name = "Off-by-One Loop Boundary"
        bug_category = "Logic Error"
        bug_location = "Range bounds in loop header (e.g., `range(1, n)`)"
        bug_severity = "Major - excludes the final required number"
        bug_explanation = (
            "Python's `range(start, stop)` function generates numbers up to, but NOT including, the `stop` value. "
            "For example, `range(1, 5)` produces `[1, 2, 3, 4]`. If your goal is to include `n` itself, "
            "the current loop stops one step too early."
        )
        hint1 = "Check whether Python's `range()` function includes or excludes the endpoint value."
        hint2 = "If a user passes `n = 5`, write down on paper the exact list of numbers your loop will visit."
        hint3 = "How can you tell `range` to stop one integer past `n` so that `n` is included in the calculations?"
    elif has_zero_div:
        bug_name = "Potential ZeroDivisionError / Unchecked Denominator"
        bug_category = "Runtime Error / Edge Case Bug"
        bug_location = "Division operation line"
        bug_severity = "Critical - crashes program when divisor is zero"
        bug_explanation = (
            "Dividing any number by zero is mathematically undefined and causes the computer to immediately raise "
            "a `ZeroDivisionError`. If the input list is empty or the quantity parameter is 0, the denominator "
            "evaluates to 0, crashing your program."
        )
        hint1 = "What happens if a user tests your program with an empty collection or with a count of 0?"
        hint2 = "Before performing division, what safety check can you perform on the denominator?"
        hint3 = "Consider using an `if` condition to verify whether the divisor is greater than 0 before dividing."
    elif has_empty_list_risk:
        bug_name = "IndexError on Empty Collection"
        bug_category = "Runtime Error"
        bug_location = "List indexing line (e.g., `numbers[0]`)"
        bug_severity = "Major - crashes when passed an empty list `[]`"
        bug_explanation = (
            "Accessing `numbers[0]` assumes that the list has at least one item. If a user calls the function "
            "with `numbers = []`, Python raises `IndexError: list index out of range`."
        )
        hint1 = "Think about what happens if someone passes an empty list with 0 items."
        hint2 = "How can you verify that a list contains elements before trying to read index 0?"
        hint3 = "Add an initial condition: `if not numbers:` or `if len(numbers) == 0:` to return a safe fallback or None."
    elif has_poor_vars:
        bug_name = "No Critical Logic Errors Detected"
        bug_category = "No Fatal Bugs"
        bug_location = "N/A"
        bug_severity = "Clean Execution"
        bug_explanation = (
            "Your calculation appears logically sound and executes without crashing. "
            "The primary improvements needed are stylistic and architectural."
        )
        hint1 = "Can someone reading your code for the first time immediately understand what `x`, `y`, and `z` represent?"
        hint2 = "Substitute single-letter names with meaningful nouns like `radius`, `pi`, and `area`."
        hint3 = "In professional engineering, code is read far more often than it is written. Clear names prevent future bugs!"
    elif is_valid_simple:
        bug_name = "No Bugs Detected! Excellent Work!"
        bug_category = "Clean Code"
        bug_location = "All lines valid"
        bug_severity = "None"
        bug_explanation = (
            "Your function is concise, valid syntactically, and correctly implements the addition logic. "
            "Both arguments are received and combined appropriately."
        )
        hint1 = "Consider adding type hints (e.g., `def add(a: float, b: float) -> float:`) to make inputs clear."
        hint2 = "Write a docstring describing what the function does and what types it expects."
        hint3 = "Test what happens if someone passes strings or negative numbers."
    else:
        bug_name = "Logical Flow / Edge Case Verification Needed"
        bug_category = "Logic / Edge Case"
        bug_location = "Main algorithm block"
        bug_severity = "Moderate"
        bug_explanation = (
            f"Reviewing your {language} implementation against the task: '{task_description}'. "
            "Ensure that variable state transitions match the intended math/logic at each iteration."
        )
        hint1 = "Trace the program step-by-step with a pencil and paper for a minimal test case."
        hint2 = "Add temporary print statements to observe how your variables change during execution."
        hint3 = "Verify whether your termination condition covers all boundary values."

    return (
        f"{demo_banner}\n\n"
        f"### 1. Overall Assessment\n"
        f"You have made a solid start on this {language} task! The structure shows you understand the general flow "
        f"of the problem. With a few targeted adjustments to edge cases and boundary conditions, your program "
        f"will be robust and ready for production.\n\n"
        f"### 2. Bugs and Errors\n"
        f"- **Error Name**: {bug_name}\n"
        f"- **Error Category**: {bug_category}\n"
        f"- **Location or Line Number**: {bug_location}\n"
        f"- **Severity**: {bug_severity}\n"
        f"- **Explanation**: {bug_explanation}\n\n"
        f"### 3. Coding Style Issues\n"
        f"- **Variable Naming**: Choose clear, descriptive names that describe the data being held.\n"
        f"- **Whitespace & Formatting**: Maintain consistent indentation and empty lines between logical blocks.\n"
        f"- **Documentation**: Add a 1-line comment or docstring stating what the function accepts and returns.\n\n"
        f"### 4. Progressive Hints\n"
        f"- **Hint 1 (Conceptual Clue)**: {hint1}\n"
        f"- **Hint 2 (Specific Guidance)**: {hint2}\n"
        f"- **Hint 3 (Strongest Clue)**: {hint3}\n\n"
        f"### 5. Suggested Test Cases\n"
        f"- **Test Case 1 (Normal Case)**:\n"
        f"  - Input: Standard positive values (e.g., `5` or `[4, 8, 2]`)\n"
        f"  - Expected Behaviour: Returns expected standard calculation accurately.\n"
        f"  - Reason for Testing: Confirms baseline functionality under typical inputs.\n"
        f"- **Test Case 2 (Edge Case)**:\n"
        f"  - Input: Boundary values (e.g., `0`, `1`, or single-element `[7]`)\n"
        f"  - Expected Behaviour: Handles boundary conditions without off-by-one errors or math exceptions.\n"
        f"  - Reason for Testing: Most computer science bugs occur at boundary conditions.\n"
        f"- **Test Case 3 (Invalid / Stress Input)**:\n"
        f"  - Input: Negative inputs, empty collection `[]`, or extreme large values.\n"
        f"  - Expected Behaviour: Handles gracefully or validates input rather than crashing unhandled.\n"
        f"  - Reason for Testing: Ensures resilience and defensive programming habits.\n\n"
        f"### 6. What To Try Next\n"
        f"1. **Manual Trace**: Step through your code by hand for a small input and verify variable values.\n"
        f"2. **Implement Guard Check**: Address the specific line highlighted in Hint 2 without rewriting the whole program.\n"
        f"3. **Run Test Cases**: Test your updated code against the Suggested Test Cases above.\n\n"
        f"*Remember: Debugging is 80% of real software engineering. Every bug you solve on your own makes you a stronger developer!*"
    )
