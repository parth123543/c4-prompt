"""Unified Code Reviewer Orchestrator for C4 Code Review Assistant."""

from __future__ import annotations
import re
from typing import Dict, Any, Optional, List, Tuple
from modules.prompt_engine import PromptEngine
from modules.openai_provider import OpenAIProvider
from modules.claude_provider import ClaudeProvider
from modules.gemini_provider import GeminiProvider
from modules.groq_provider import GroqProvider


class CodeReviewer:
    """Orchestrates input validation, prompt construction, LLM provider routing,

    response parsing, and pedagogical compliance auditing.
    """

    SUPPORTED_LANGUAGES = ["Python", "Java", "C", "C++", "JavaScript"]

    SAMPLE_PROGRAMS = {
        "Python": {
            "title": "Sum from 1 to N (Off-by-one Bug)",
            "task": "Write a function that calculates the sum of all integers from 1 up to and including n.",
            "code": (
                "def sum_to_n(n):\n"
                "    total = 0\n"
                "    for i in range(1, n):\n"
                "        total += i\n"
                "    return total\n\n"
                "# Test call\n"
                "print('Sum to 5 should be 15:', sum_to_n(5))\n"
            )
        },
        "Java": {
            "title": "Array Average with Division Issue",
            "task": "Calculate and return the average of integer values in an array.",
            "code": (
                "public class AverageCalculator {\n"
                "    public static double calculateAverage(int[] numbers) {\n"
                "        int sum = 0;\n"
                "        for (int i = 0; i <= numbers.length; i++) {\n"
                "            sum += numbers[i];\n"
                "        }\n"
                "        return sum / numbers.length;\n"
                "    }\n"
                "}\n"
            )
        },
        "C": {
            "title": "Factorial with Zero Initialization",
            "task": "Compute the factorial of a given integer n.",
            "code": (
                "#include <stdio.h>\n\n"
                "int factorial(int n) {\n"
                "    int result = 0; // Notice initialization\n"
                "    for (int i = 1; i <= n; i++) {\n"
                "        result *= i;\n"
                "    }\n"
                "    return result;\n"
                "}\n\n"
                "int main() {\n"
                "    printf(\"Factorial of 5: %d\\n\", factorial(5));\n"
                "    return 0;\n"
                "}\n"
            )
        },
        "C++": {
            "title": "Find Maximum with Empty Vector Risk",
            "task": "Find and return the maximum element in a vector of integers.",
            "code": (
                "#include <iostream>\n"
                "#include <vector>\n\n"
                "int findMax(const std::vector<int>& nums) {\n"
                "    int maxVal = nums[0]; // What if nums is empty?\n"
                "    for (size_t i = 0; i < nums.size(); ++i) {\n"
                "        if (nums[i] > maxVal) {\n"
                "            maxVal = nums[i];\n"
                "        }\n"
                "    }\n"
                "    return maxVal;\n"
                "}\n"
            )
        },
        "JavaScript": {
            "title": "Filter Active Users with Type Equality Bug",
            "task": "Filter a list of user objects and return names of users with active status.",
            "code": (
                "function getActiveUserNames(users) {\n"
                "    let active = [];\n"
                "    for (let i = 0; i < users.length; i++) {\n"
                "        // Notice condition check\n"
                "        if (users[i].status = 'active') {\n"
                "            active.push(users[i].name);\n"
                "        }\n"
                "    }\n"
                "    return active;\n"
                "}\n"
            )
        }
    }

    def __init__(self, prompts_dir: Optional[str] = None):
        self.prompt_engine = PromptEngine(prompts_dir=prompts_dir)
        self.openai_provider = OpenAIProvider()
        self.claude_provider = ClaudeProvider()
        self.gemini_provider = GeminiProvider()
        self.groq_provider = GroqProvider()

    def update_api_keys(
        self,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        gemini_key: Optional[str] = None,
        groq_key: Optional[str] = None
    ) -> None:
        """Dynamically reconfigures API keys from UI inputs or environment."""
        if openai_key is not None:
            self.openai_provider = OpenAIProvider(api_key=openai_key)
        if anthropic_key is not None:
            self.claude_provider = ClaudeProvider(api_key=anthropic_key)
        if gemini_key is not None:
            self.gemini_provider = GeminiProvider(api_key=gemini_key)
        if groq_key is not None:
            self.groq_provider = GroqProvider(api_key=groq_key)

    def get_sample_code(self, language: str) -> Dict[str, str]:
        """Returns sample code and task for the requested language."""
        lang_title = (language or "Python").capitalize()
        return self.SAMPLE_PROGRAMS.get(
            lang_title,
            self.SAMPLE_PROGRAMS["Python"]
        )

    def validate_submission(self, code: str, task: str) -> Tuple[bool, str]:
        """Validates student inputs before dispatching."""
        return self.prompt_engine.validate_code_input(code, task)

    def review(
        self,
        language: str,
        task_description: str,
        code: str,
        provider_name: str = "Gemini",
        model: Optional[str] = None,
        prompt_version: str = "v3",
        temperature: float = 0.2,
        demo_fallback: bool = True
    ) -> Dict[str, Any]:
        """Dispatches code review to the selected provider with prompt engineering."""
        # 1. Input Validation
        is_valid, err_msg = self.validate_submission(code, task_description)
        if not is_valid:
            return {
                "success": False,
                "error": err_msg,
                "provider": provider_name,
                "model": model or "N/A",
                "parsed_sections": {},
                "raw_content": "",
                "compliance": {"compliant": True, "details": "Validation failed before execution."}
            }

        # 2. Prepare Prompts
        system_prompt = self.prompt_engine.get_system_prompt(version=prompt_version)
        user_prompt = self.prompt_engine.build_user_prompt(
            language=language,
            task_description=task_description,
            student_code=code
        )

        context = {
            "language": language,
            "task_description": task_description,
            "code": code,
            "prompt_version": prompt_version
        }

        # 3. Provider Routing
        provider_lower = (provider_name or "gemini").lower()
        if "groq" in provider_lower:
            target_model = model or "qwen/qwen3.8-27b"
            result = self.groq_provider.review_code(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=target_model,
                temperature=temperature,
                demo_fallback=demo_fallback,
                context=context
            )
        elif "openai" in provider_lower or "chatgpt" in provider_lower:
            target_model = model or "gpt-4o-mini"
            result = self.openai_provider.review_code(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=target_model,
                temperature=temperature,
                demo_fallback=demo_fallback,
                context=context
            )
        elif "claude" in provider_lower or "anthropic" in provider_lower:
            target_model = model or "claude-3-5-sonnet-20241022"
            result = self.claude_provider.review_code(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=target_model,
                temperature=temperature,
                demo_fallback=demo_fallback,
                context=context
            )
        else:  # Gemini default
            target_model = model or "gemini-2.5-flash"
            result = self.gemini_provider.review_code(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=target_model,
                temperature=temperature,
                demo_fallback=demo_fallback,
                context=context
            )

        if result.get("error"):
            return {
                "success": False,
                "error": result["error"],
                "provider": result.get("provider", provider_name),
                "model": result.get("model", target_model),
                "parsed_sections": {},
                "raw_content": "",
                "compliance": {"compliant": True, "details": "Error occurred during provider execution."}
            }

        raw_content = result.get("content", "")

        # 4. Parse Structured Output Sections
        parsed_sections = self.parse_sections(raw_content)

        # 5. Check No Full Solution Compliance
        compliance = self.prompt_engine.check_solution_leakage(raw_content, code)

        return {
            "success": True,
            "provider": result.get("provider", provider_name),
            "model": result.get("model", target_model),
            "is_demo": result.get("is_demo", False),
            "notice": result.get("notice", None),
            "tokens": result.get("tokens", {}),
            "raw_content": raw_content,
            "parsed_sections": parsed_sections,
            "compliance": compliance,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }

    def compare_all(
        self,
        language: str,
        task_description: str,
        code: str,
        prompt_version: str = "v3",
        demo_fallback: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Runs the review across ChatGPT, Claude, and Gemini for side-by-side comparison."""
        results = {}
        providers = [
            ("Gemini", "gemini-2.5-flash"),
            ("Groq", "qwen/qwen3.8-27b"),
            ("ChatGPT", "gpt-4o-mini")
        ]

        for prov, mod in providers:
            res = self.review(
                language=language,
                task_description=task_description,
                code=code,
                provider_name=prov,
                model=mod,
                prompt_version=prompt_version,
                demo_fallback=demo_fallback
            )
            results[prov] = res

        return results

    @staticmethod
    def parse_sections(markdown_text: str) -> Dict[str, Any]:
        """Parses C4 structured markdown headings into modular UI sections."""
        sections = {
            "assessment": "",
            "bugs": "",
            "style": "",
            "hints": "",
            "hint_1": "",
            "hint_2": "",
            "hint_3": "",
            "test_cases": "",
            "next_steps": "",
            "other": ""
        }

        if not markdown_text:
            return sections

        # Clean demo banner if present for section parsing
        content = re.sub(r"^>\s*⚠️[\s\S]*?\n\n", "", markdown_text).strip()

        # Regular expressions to locate standard C4 section headers
        patterns = [
            ("assessment", r"###?\s*1\.?\s*Overall Assessment([\s\S]*?)(?=###?\s*2|$)", 1),
            ("bugs", r"###?\s*2\.?\s*Bugs and Errors([\s\S]*?)(?=###?\s*3|$)", 1),
            ("style", r"###?\s*3\.?\s*Coding Style Issues([\s\S]*?)(?=###?\s*4|$)", 1),
            ("hints", r"###?\s*4\.?\s*Progressive Hints([\s\S]*?)(?=###?\s*5|$)", 1),
            ("test_cases", r"###?\s*5\.?\s*Suggested Test Cases([\s\S]*?)(?=###?\s*6|$)", 1),
            ("next_steps", r"###?\s*6\.?\s*What To Try Next([\s\S]*?)$", 1),
        ]

        found_any = False
        for sec_name, pat, group_idx in patterns:
            match = re.search(pat, content, re.IGNORECASE)
            if match:
                found_any = True
                sections[sec_name] = match.group(group_idx).strip()

        # If hints were found, extract Hint 1, Hint 2, Hint 3
        if sections["hints"]:
            h1 = re.search(r"\*\*Hint 1[^\*]*\*\*[:\s]*([\s\S]*?)(?=\*\*Hint 2|$)", sections["hints"], re.IGNORECASE)
            h2 = re.search(r"\*\*Hint 2[^\*]*\*\*[:\s]*([\s\S]*?)(?=\*\*Hint 3|$)", sections["hints"], re.IGNORECASE)
            h3 = re.search(r"\*\*Hint 3[^\*]*\*\*[:\s]*([\s\S]*?)$", sections["hints"], re.IGNORECASE)

            if h1:
                sections["hint_1"] = h1.group(1).strip()
            if h2:
                sections["hint_2"] = h2.group(1).strip()
            if h3:
                sections["hint_3"] = h3.group(1).strip()

        # If none of the 6 headings matched (e.g. V1/V2 or unformatted response), put in assessment/other
        if not found_any:
            sections["assessment"] = markdown_text

        return sections
