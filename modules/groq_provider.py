"""Groq Cloud API Provider for C4 Code Review Assistant."""

from __future__ import annotations
import os
import time
from typing import Dict, Any, Optional
from modules.demo_generator import generate_demo_review

try:
    from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
except ImportError:
    OpenAI = None
    AuthenticationError = RateLimitError = APIConnectionError = Exception


class GroqProvider:
    """Manages Groq Cloud API integration using OpenAI-compatible interface."""

    AVAILABLE_MODELS = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "allam-2-7b"
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "").strip()
        self.client = None
        if self.is_configured() and OpenAI is not None:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
            except Exception:
                self.client = None

    def is_configured(self) -> bool:
        """Returns True if a real API key is present."""
        if not self.api_key:
            return False
        if any(placeholder in self.api_key.lower() for placeholder in ["your_", "placeholder", "key_here"]):
            return False
        return len(self.api_key) > 10

    def review_code(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "qwen/qwen3.8-27b",
        temperature: float = 0.2,
        max_retries: int = 2,
        demo_fallback: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submits code review prompt to Groq and returns structured result."""
        context = context or {}
        language = context.get("language", "Python")
        task_desc = context.get("task_description", "")
        code = context.get("code", "")
        prompt_version = context.get("prompt_version", "v3")

        if not self.is_configured():
            if demo_fallback:
                simulated_text = generate_demo_review(
                    provider_name="Groq (Cloud LPU)",
                    language=language,
                    task_description=task_desc,
                    code=code,
                    prompt_version=prompt_version
                )
                return {
                    "provider": "Groq",
                    "model": f"{model} (Demo Mode)",
                    "content": simulated_text,
                    "is_demo": True,
                    "tokens": {"prompt": 0, "completion": 0, "total": 0},
                    "error": None,
                    "notice": "Using Simulated Demo Mode: GROQ_API_KEY is not configured in .env or settings."
                }
            return {
                "provider": "Groq",
                "model": model,
                "content": "",
                "is_demo": False,
                "error": "Groq API key is missing. Please set GROQ_API_KEY in your .env file or UI settings."
            }

        if self.client is None and OpenAI is not None:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )

        attempts = 0
        last_error = ""

        # Normalize model
        target_model = model
        if target_model not in self.AVAILABLE_MODELS and not any(p in target_model for p in ["qwen", "llama", "gpt-oss", "allam"]):
            target_model = "qwen/qwen3.8-27b"

        while attempts <= max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    timeout=30.0
                )

                content = response.choices[0].message.content or ""
                usage = getattr(response, "usage", None)
                tokens = {
                    "prompt": usage.prompt_tokens if usage else 0,
                    "completion": usage.completion_tokens if usage else 0,
                    "total": usage.total_tokens if usage else 0,
                }

                return {
                    "provider": "Groq",
                    "model": target_model,
                    "content": content,
                    "is_demo": False,
                    "tokens": tokens,
                    "error": None
                }

            except AuthenticationError as e:
                return {
                    "provider": "Groq",
                    "model": target_model,
                    "content": "",
                    "is_demo": False,
                    "error": f"Groq Authentication Failed: Invalid API key ({str(e)})."
                }
            except RateLimitError as e:
                attempts += 1
                last_error = f"Groq Rate limit exceeded: {str(e)}"
                if attempts <= max_retries:
                    time.sleep(2 * attempts)
                    continue
            except APIConnectionError as e:
                attempts += 1
                last_error = f"Network connection error contacting Groq: {str(e)}"
                if attempts <= max_retries:
                    time.sleep(1.5 * attempts)
                    continue
            except Exception as e:
                return {
                    "provider": "Groq",
                    "model": target_model,
                    "content": "",
                    "is_demo": False,
                    "error": f"Groq API Error: {str(e)}"
                }

        if demo_fallback:
            simulated_text = generate_demo_review(
                provider_name="Groq (Cloud LPU)",
                language=language,
                task_description=task_desc,
                code=code,
                prompt_version=prompt_version
            )
            return {
                "provider": "Groq",
                "model": f"{target_model} (Demo Fallback)",
                "content": simulated_text,
                "is_demo": True,
                "error": None,
                "notice": f"Live Groq request failed ({last_error}). Reverted to Demo Mode."
            }

        return {
            "provider": "Groq",
            "model": target_model,
            "content": "",
            "is_demo": False,
            "error": last_error
        }
