"""Prompt Engineering System for C4 Code Review Assistant.

Manages prompt versions (V1 Baseline, V2 Improved, V3 Final), formats prompt
payloads, and validates prompt inputs and outputs.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


class PromptEngine:
    """Manages system and user prompts across pedagogical iterations."""

    PROMPT_VERSIONS = ["v1", "v2", "v3", "final"]

    def __init__(self, prompts_dir: Optional[str] = None):
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            # Default to project root prompts directory
            base_dir = Path(__file__).resolve().parent.parent
            self.prompts_dir = base_dir / "prompts"

    def get_system_prompt(self, version: str = "v3") -> str:
        """Loads system prompt for the specified version.

        Falls back to hardcoded prompts if file is missing.
        """
        ver_normalized = version.lower().strip()
        if ver_normalized not in self.PROMPT_VERSIONS:
            ver_normalized = "v3"

        prompt_file = self.prompts_dir / ver_normalized / "system_prompt.txt"
        if prompt_file.exists():
            try:
                return prompt_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        # Fallback system prompts
        if ver_normalized == "v1":
            return (
                "You are an AI code reviewer. Your job is to review the user's code for any syntax errors, "
                "runtime errors, logical bugs, and style issues. Provide a clear analysis of any errors found "
                "and suggest fixes so the student can make their code work."
            )
        elif ver_normalized == "v2":
            return (
                "You are C4, a patient and supportive programming mentor dedicated to helping first-year "
                "computer science students learn how to code and debug.\n\n"
                "CORE CONSTRAINTS:\n"
                "1. NEVER provide the complete corrected program.\n"
                "2. NEVER provide a complete replacement function that solves the student's task.\n"
                "3. Do not directly reveal the final code answer.\n"
                "4. Explain all errors in beginner-friendly, accessible language.\n"
                "5. Guide the student so they think critically and learn how to fix the problem themselves."
            )
        else:  # v3 and final
            return (
                "ROLE PROMPTING:\n"
                "You are C4, a patient and experienced programming mentor who teaches first-year students. "
                "Your mission is to help students learn to think like software engineers, debug their own code, "
                "and build deep problem-solving skills rather than relying on copy-pasting solutions.\n\n"
                "STRICT CONSTRAINTS:\n"
                "1. Never provide the complete corrected program.\n"
                "2. Never provide a complete replacement function that solves the entire task.\n"
                "3. Do not reveal the direct final answer.\n"
                "4. Explain errors in beginner-friendly language, breaking down confusing terms with intuitive analogies.\n"
                "5. Do not invent errors. If the code is correct, celebrate the student's success!\n"
                "6. Distinguish confirmed errors from possible issues.\n"
                "7. If the task description is insufficient or ambiguous, politely request clarification from the student.\n"
                "8. Encourage students to debug independently by posing thought-provoking questions.\n"
                "9. Never claim code was executed unless it actually was. Clarify that analysis is static.\n\n"
                "REQUIRED STRUCTURED OUTPUT FORMAT:\n"
                "### 1. Overall Assessment\n"
                "### 2. Bugs and Errors\n"
                "### 3. Coding Style Issues\n"
                "### 4. Progressive Hints\n"
                "### 5. Suggested Test Cases\n"
                "### 6. What To Try Next\n"
            )

    def build_user_prompt(
        self,
        language: str,
        task_description: str,
        student_code: str,
        extra_context: str = ""
    ) -> str:
        """Formats the input into a standard mentor prompt."""
        lang_clean = (language or "Python").strip().capitalize()
        task_clean = (task_description or "Not specified by student.").strip()
        code_clean = (student_code or "").strip()

        prompt = (
            f"STUDENT PROGRAMMING LANGUAGE: {lang_clean}\n\n"
            f"STUDENT'S TASK DESCRIPTION:\n{task_clean}\n\n"
            f"STUDENT'S CODE TO REVIEW:\n"
            f"```{lang_clean.lower()}\n"
            f"{code_clean}\n"
            f"```\n\n"
            f"MENTOR INSTRUCTION:\n"
            f"Review this {lang_clean} code according to your mentor guidelines and strict constraints. "
            f"Remember: Do NOT output the complete corrected program or complete solution function. "
            f"Guide the student with structured feedback and progressive hints."
        )

        if extra_context.strip():
            prompt += f"\n\nADDITIONAL STUDENT CONTEXT:\n{extra_context.strip()}"

        return prompt

    def get_experiment_metadata(self) -> Dict[str, Dict[str, str]]:
        """Returns comparison metadata for Prompt Experimentation."""
        return {
            "v1": {
                "name": "V1 – Baseline",
                "tag": "Standard Assistant Prompt",
                "what_changed": "Baseline instructions: Simple code review request without role persona or constraints.",
                "reason": "Establishes reference behavior of standard LLMs, which typically generate full solution code directly.",
                "pedagogical_flaw": "Students copy-paste complete code without understanding the underlying flaw or building debugging skills.",
                "expected_result": "Produces a direct corrected code block, depriving the student of active learning."
            },
            "v2": {
                "name": "V2 – Improved",
                "tag": "Role Prompting + Negative Constraints",
                "what_changed": "Introduced 'C4' mentor persona and explicit negative constraints ('NEVER provide full solution').",
                "reason": "Prevents answer-leaking and shifts tone to empathetic, beginner-friendly explanations.",
                "pedagogical_flaw": "Unstructured output can be overwhelming or inconsistent in depth across different runs.",
                "expected_result": "Refuses full solution and explains bugs, but lacks staged hints and systematic test case design."
            },
            "v3": {
                "name": "V3 – Final (C4 Standard)",
                "tag": "Structured Output + Progressive Hints + Boundary Testing",
                "what_changed": (
                    "Added 9 strict constraints, 6 structured markdown sections (Assessment, Bugs, Style, "
                    "3 Progressive Hints, 3 Concrete Test Cases, What To Try Next), and clarification handling."
                ),
                "reason": (
                    "Maximizes educational value through Socratic progressive disclosure (Hint 1 -> Hint 2 -> Hint 3) "
                    "and teaches students how to test edge cases systematically."
                ),
                "pedagogical_flaw": "None. Fully aligns with college computer science pedagogy.",
                "expected_result": (
                    "Consistent, predictable, structured response with no code leakage, 3-tier hints, "
                    "and test cases with inputs, expected behavior, and testing reasons."
                )
            }
        }

    @staticmethod
    def validate_code_input(code: str, task_description: str = "") -> Tuple[bool, str]:
        """Validates student code submission before dispatching to LLM.

        Returns (is_valid, error_message).
        """
        if not code or not code.strip():
            return False, "Code submission is empty. Please write or paste your code before requesting a review."

        clean_code = code.strip()

        if len(clean_code) < 5:
            return False, "Code snippet is too short to review. Please enter at least one valid statement."

        # Detect random keyboard smashing (e.g., 'asdkjasd qwerty zxcvbnm')
        words = clean_code.split()
        if len(words) >= 4:
            has_keywords = any(
                kw in clean_code for kw in [
                    "def", "class", "import", "return", "if", "for", "while",
                    "print", "int", "void", "public", "function", "var", "let",
                    "const", "include", "std", "{", "}", ";", "(", ")", "=", ":"
                ]
            )
            has_common_chars = bool(re.search(r"[{}();=+\-*/<>]", clean_code))
            if not has_keywords and not has_common_chars:
                avg_len = sum(len(w) for w in words) / len(words)
                if avg_len > 7:
                    return False, (
                        "Input appears to be random text rather than valid source code. "
                        "Please provide code written in Python, Java, C, C++, or JavaScript."
                    )

        return True, ""

    @staticmethod
    def check_solution_leakage(response_text: str, student_code: str) -> Dict[str, Any]:
        """Audits the model response to check compliance with the 'No Full Solution' rule.

        Returns a dictionary with compliance metrics.
        """
        if not response_text:
            return {"compliant": True, "details": "Empty response"}

        # Extract markdown code blocks
        code_blocks = re.findall(r"```(?:\w+)?\n([\s\S]*?)```", response_text)

        leaked_full_program = False
        reasons = []

        total_student_lines = max(1, len([l for l in student_code.strip().splitlines() if l.strip()]))

        for block in code_blocks:
            block_lines = [l for l in block.strip().splitlines() if l.strip()]
            # If block has more than 8 lines and contains full structure definitions
            if len(block_lines) >= total_student_lines and len(block_lines) >= 6:
                if any(kw in block for kw in ["def ", "class ", "int main", "function "]):
                    leaked_full_program = True
                    reasons.append("Contains a complete replacement function or program block.")
                    break

        # Check for phrase leakage
        leak_phrases = [
            "here is the complete corrected code",
            "here is the full solution",
            "here is the corrected program",
            "copy and paste this solution",
            "here is the fixed code:",
        ]
        for phrase in leak_phrases:
            if phrase in response_text.lower():
                leaked_full_program = True
                reasons.append(f"Contains revealing phrase: '{phrase}'")

        return {
            "compliant": not leaked_full_program,
            "leakage_detected": leaked_full_program,
            "code_blocks_count": len(code_blocks),
            "reasons": reasons if reasons else ["Response complied with no-complete-solution restriction."]
        }
