"""Google Gemini API Provider for C4 Code Review Assistant."""

from __future__ import annotations
import os
import time
from typing import Dict, Any, Optional
from modules.demo_generator import generate_demo_review

try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
except ImportError:
    genai = None
    types = None
    APIError = Exception


class GeminiProvider:
    """Manages Google Gemini API integration using the official Google GenAI Python SDK."""

    AVAILABLE_MODELS = [
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY", "").strip()
            or os.getenv("GOOGLE_API_KEY", "").strip()
        )
        self.client = None
        if self.is_configured() and genai is not None:
            try:
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options={"api_version": "v1beta"}
                )
            except Exception:
                self.client = None

    def is_configured(self) -> bool:
        """Returns True if a real API key is present and not a dummy placeholder."""
        if not self.api_key:
            return False
        if any(placeholder in self.api_key.lower() for placeholder in ["your_", "placeholder", "key_here", "ai-xxx"]):
            return False
        return len(self.api_key) > 10

    def review_code(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        max_retries: int = 2,
        demo_fallback: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submits code review prompt to Google Gemini and returns structured result."""
        context = context or {}
        language = context.get("language", "Python")
        task_desc = context.get("task_description", "")
        code = context.get("code", "")
        prompt_version = context.get("prompt_version", "v3")

        # Fallback to demo mode if not configured
        if not self.is_configured():
            if demo_fallback:
                simulated_text = generate_demo_review(
                    provider_name="Gemini (Google DeepMind)",
                    language=language,
                    task_description=task_desc,
                    code=code,
                    prompt_version=prompt_version
                )
                return {
                    "provider": "Google Gemini",
                    "model": f"{model} (Demo Mode)",
                    "content": simulated_text,
                    "is_demo": True,
                    "tokens": {"prompt": 0, "completion": 0, "total": 0},
                    "error": None,
                    "notice": "Using Simulated Demo Mode: GEMINI_API_KEY is not configured in .env or settings."
                }
            return {
                "provider": "Google Gemini",
                "model": model,
                "content": "",
                "is_demo": False,
                "error": "Gemini API key is missing. Please set GEMINI_API_KEY in your .env file or UI settings."
            }

        if self.client is None and genai is not None:
            self.client = genai.Client(
                api_key=self.api_key,
                http_options={"api_version": "v1beta"}
            )

        attempts = 0
        last_error = ""

        # Normalize model name if needed
        model_name = model
        if not model_name.startswith("gemini-"):
            model_name = "gemini-2.5-flash"

        while attempts <= max_retries:
            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                )
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=config
                )

                content = response.text or ""
                metadata = getattr(response, "usage_metadata", None)
                tokens = {
                    "prompt": getattr(metadata, "prompt_token_count", 0) if metadata else 0,
                    "completion": getattr(metadata, "candidates_token_count", 0) if metadata else 0,
                    "total": getattr(metadata, "total_token_count", 0) if metadata else 0,
                }

                return {
                    "provider": "Google Gemini",
                    "model": model_name,
                    "content": content,
                    "is_demo": False,
                    "tokens": tokens,
                    "error": None
                }

            except Exception as e:
                err_str = str(e)
                if "API_KEY_INVALID" in err_str or "401" in err_str or "unregistered" in err_str.lower():
                    return {
                        "provider": "Google Gemini",
                        "model": model_name,
                        "content": "",
                        "is_demo": False,
                        "error": f"Google Gemini Authentication Failed: Invalid API key ({err_str}). Get a valid key at https://aistudio.google.com/app/apikey"
                    }
                elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    attempts += 1
                    last_error = f"Gemini quota or rate limit exceeded: {err_str}"
                    if attempts <= max_retries:
                        time.sleep(2 * attempts)
                        continue
                else:
                    attempts += 1
                    last_error = f"Google Gemini API error: {err_str}"
                    if attempts <= max_retries:
                        time.sleep(1.5 * attempts)
                        continue

        # If retries exhausted and demo fallback allowed
        if demo_fallback:
            simulated_text = generate_demo_review(
                provider_name="Gemini (Google DeepMind)",
                language=language,
                task_description=task_desc,
                code=code,
                prompt_version=prompt_version
            )
            return {
                "provider": "Google Gemini",
                "model": f"{model_name} (Demo Fallback)",
                "content": simulated_text,
                "is_demo": True,
                "error": None,
                "notice": f"Live Gemini request failed ({last_error}). Reverted to Demo Mode."
            }

        return {
            "provider": "Google Gemini",
            "model": model_name,
            "content": "",
            "is_demo": False,
            "error": last_error
        }
