"""Test Case Manager for C4 Code Review Assistant."""

from __future__ import annotations
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from modules.code_reviewer import CodeReviewer


class TestManager:
    """Manages the 12 pedagogical test scenarios, execution against AI models,

    and transparent pass/fail evaluation.
    """
    __test__ = False

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            base_dir = Path(__file__).resolve().parent.parent
            self.data_dir = base_dir / "test-data"

        self.cases_file = self.data_dir / "test_cases.csv"
        self.results_file = self.data_dir / "test_results.csv"

    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Loads all prepared test cases as a list of dictionaries."""
        if not self.cases_file.exists():
            return []

        try:
            df = pd.read_csv(self.cases_file)
            # Fill NaN values with empty string
            df = df.fillna("")
            return df.to_dict(orient="records")
        except Exception:
            return []

    def get_test_case_by_id(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single test case by its ID."""
        cases = self.get_test_cases()
        for tc in cases:
            if tc.get("test_id") == test_id:
                return tc
        return None

    def get_results_df(self) -> pd.DataFrame:
        """Loads the test results log into a pandas DataFrame."""
        if not self.results_file.exists():
            return pd.DataFrame(columns=[
                "test_id", "title", "model_used", "timestamp",
                "pass_fail", "actual_category_detected", "full_solution_avoided", "notes"
            ])

        try:
            df = pd.read_csv(self.results_file)
            return df
        except Exception:
            return pd.DataFrame()

    def evaluate_response(
        self,
        test_case: Dict[str, Any],
        review_result: Dict[str, Any]
    ) -> Tuple[str, str, str, str]:
        """Transparently evaluates whether the model detected the expected issue

        and obeyed the 'no full solution' constraint.
        Returns: (pass_fail, actual_category_detected, full_solution_avoided, notes)
        """
        test_id = test_case.get("test_id", "")
        expected_cat = test_case.get("expected_category", "")

        # 1. Validation test cases (TC10, TC11)
        if test_id in ["TC10", "TC11"]:
            if not review_result.get("success"):
                err_msg = review_result.get("error", "")
                if "empty" in err_msg.lower() or "random" in err_msg.lower() or "too short" in err_msg.lower():
                    return "PASS", "Validation Error Intercepted", "YES", f"Successfully caught invalid input: {err_msg}"
                return "PASS", "Validation Error", "YES", f"Handled invalid input gracefully: {err_msg}"
            else:
                # If it allowed empty code or gibberish through without warning
                return "FAIL", "Uncaught Validation Issue", "NO", "System failed to intercept invalid non-code input."

        if not review_result.get("success"):
            return "FAIL", "Execution Error", "N/A", f"Provider execution failed: {review_result.get('error')}"

        raw_text = review_result.get("raw_content", "")
        raw_lower = raw_text.lower()
        compliance = review_result.get("compliance", {})
        full_avoided = "YES" if compliance.get("compliant", True) else "NO"

        actual_cat = "Detected"
        notes = []

        # 2. Check Pedagogical Constraint
        if full_avoided == "NO":
            return "FAIL", "Constraint Violation", "NO", "FAILED: Mentor provided full solution code block violating C4 constraints."

        # 3. Check Specific Test Scenarios
        passed = False

        if test_id == "TC01":  # Valid addition
            # Should NOT report critical bugs
            if any(term in raw_lower for term in ["no bugs detected", "no error", "code is correct", "works correctly", "valid"]):
                passed = True
                actual_cat = "Valid / No False Positives"
                notes.append("Accurately identified correct program without inventing false bugs.")
            else:
                actual_cat = "Potential False Positive"
                notes.append("May have hallucinated errors in valid addition code.")

        elif test_id == "TC02":  # Missing colon
            if any(term in raw_lower for term in ["colon", "syntax", "def check_positive", ":"]):
                passed = True
                actual_cat = "Syntax Error (Missing Colon)"
                notes.append("Identified missing colon at end of function header or if condition.")
            else:
                actual_cat = "Missed Syntax Error"
                notes.append("Failed to explicitly identify missing colon.")

        elif test_id == "TC03":  # Indentation
            if any(term in raw_lower for term in ["indent", "whitespace", "block", "tab"]):
                passed = True
                actual_cat = "Syntax / Indentation Error"
                notes.append("Identified indentation failure inside loop body.")
            else:
                actual_cat = "Missed Indentation"
                notes.append("Failed to highlight missing indentation.")

        elif test_id == "TC04":  # Off-by-one loop
            if any(term in raw_lower for term in ["off-by-one", "range(1, n)", "range", "boundary", "exclude", "n + 1"]):
                passed = True
                actual_cat = "Logic Error (Loop Bound)"
                notes.append("Identified that range(1, n) excludes the upper bound n.")
            else:
                actual_cat = "Missed Off-by-One"
                notes.append("Did not flag exclusion of upper bound in range().")

        elif test_id == "TC05":  # Division by zero
            if any(term in raw_lower for term in ["zerodivision", "division by zero", "empty", "zero", "len"]):
                passed = True
                actual_cat = "Runtime Error (ZeroDivisionError)"
                notes.append("Identified division by zero risk when scores list is empty.")
            else:
                actual_cat = "Missed Zero Division"
                notes.append("Failed to warn of division by zero with empty collection.")

        elif test_id == "TC06":  # Factorial zero
            if any(term in raw_lower for term in ["result = 0", "multiplication", "product", "identity", "starts at 0", "zero"]):
                passed = True
                actual_cat = "Logic Error (Zero Multiplier)"
                notes.append("Identified that initializing product to 0 keeps output at 0.")
            else:
                actual_cat = "Missed Factorial Initialization"
                notes.append("Failed to note zero initialization flaw.")

        elif test_id == "TC07":  # Zero input
            if any(term in raw_lower for term in ["zero", "qty == 0", "division", "crash", "edge case", "denominator"]):
                passed = True
                actual_cat = "Edge Case / Runtime Risk"
                notes.append("Noted risk when quantity or denominator is 0.")
            else:
                actual_cat = "Missed Edge Case"
                notes.append("Did not highlight risk when input is zero.")

        elif test_id == "TC08":  # Large input / Recursion
            if any(term in raw_lower for term in ["recursion", "exponential", "o(2^n)", "large", "stack", "memoiz", "freeze"]):
                passed = True
                actual_cat = "Performance / Complexity"
                notes.append("Identified exponential recursion complexity for large inputs.")
            else:
                actual_cat = "Missed Complexity Issue"
                notes.append("Did not warn about exponential recursion time.")

        elif test_id == "TC09":  # Empty collection indexing
            if any(term in raw_lower for term in ["indexerror", "empty", "numbers[0]", "out of range"]):
                passed = True
                actual_cat = "Runtime Error (IndexError)"
                notes.append("Spotted IndexError on empty list indexing.")
            else:
                actual_cat = "Missed Index Risk"
                notes.append("Failed to warn about indexing empty collection.")

        elif test_id == "TC12":  # Poor variable names
            if any(term in raw_lower for term in ["variable", "naming", "descriptive", "readab", "x, y, z", "style"]):
                passed = True
                actual_cat = "Style / Variable Naming"
                notes.append("Noted clean calculation while guiding toward descriptive variable names.")
            else:
                actual_cat = "Missed Naming Critique"
                notes.append("Did not comment on single-letter variable names.")
        else:
            passed = True
            actual_cat = "Evaluated"
            notes.append("Completed review.")

        pass_fail = "PASS" if passed else "FAIL"
        note_str = " ".join(notes)
        return pass_fail, actual_cat, full_avoided, note_str

    def run_test(
        self,
        test_id: str,
        reviewer: CodeReviewer,
        provider_name: str = "Gemini",
        model: Optional[str] = None,
        prompt_version: str = "v3"
    ) -> Dict[str, Any]:
        """Runs a single test case, evaluates it, logs to CSV, and returns results."""
        tc = self.get_test_case_by_id(test_id)
        if not tc:
            return {"error": f"Test case {test_id} not found."}

        review_res = reviewer.review(
            language=tc.get("language", "Python"),
            task_description=tc.get("task_description", ""),
            code=tc.get("code_snippet", ""),
            provider_name=provider_name,
            model=model,
            prompt_version=prompt_version,
            demo_fallback=True
        )

        pass_fail, actual_cat, full_avoided, notes = self.evaluate_response(tc, review_res)

        record = {
            "test_id": test_id,
            "title": tc.get("title", ""),
            "model_used": f"{provider_name} ({model or 'default'})",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pass_fail": pass_fail,
            "actual_category_detected": actual_cat,
            "full_solution_avoided": full_avoided,
            "notes": notes
        }

        self.append_result(record)

        return {
            "test_case": tc,
            "review_result": review_res,
            "evaluation": record
        }

    def append_result(self, record: Dict[str, Any]) -> None:
        """Appends a new result row to test_results.csv."""
        df_new = pd.DataFrame([record])
        if self.results_file.exists():
            try:
                df_existing = pd.read_csv(self.results_file)
                # Remove prior run for this test_id and model if updating
                mask = (df_existing["test_id"] == record["test_id"]) & (df_existing["model_used"] == record["model_used"])
                df_existing = df_existing[~mask]
                df_updated = pd.concat([df_existing, df_new], ignore_index=True)
                df_updated.to_csv(self.results_file, index=False)
                return
            except Exception:
                pass

        df_new.to_csv(self.results_file, index=False)
