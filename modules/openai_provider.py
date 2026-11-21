"""OpenAI / ChatGPT API Provider for C4 Code Review Assistant."""

from __future__ import annotations
import os
import time
from typing import Dict, Any, Optional
from modules.demo_generator import generate_demo_review

try:
    from openai import OpenAI, OpenAIError, AuthenticationError, RateLimitError, APIConnectionError
except ImportError:
    OpenAI = None
    OpenAIError = Exception


class OpenAIProvider:
    """Manages ChatGPT API integration using the official OpenAI Python SDK."""

    AVAILABLE_MODELS = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-3.5-turbo"
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "").strip()
        self.client = None
        if self.is_configured() and OpenAI is not None:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception:
                self.client = None

    def is_configured(self) -> bool:
        """Returns True if a real API key is present and not a dummy placeholder."""
        if not self.api_key:
            return False
        if any(placeholder in self.api_key.lower() for placeholder in ["your_", "placeholder", "key_here", "sk-xxx"]):
            return False
        return len(self.api_key) > 10

    def review_code(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        max_retries: int = 2,
        demo_fallback: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submits code review prompt to OpenAI and returns structured result."""
        context = context or {}
        language = context.get("language", "Python")
        task_desc = context.get("task_description", "")
        code = context.get("code", "")
        prompt_version = context.get("prompt_version", "v3")

        # Fallback to demo mode if not configured
        if not self.is_configured():
            if demo_fallback:
                simulated_text = generate_demo_review(
                    provider_name="ChatGPT (OpenAI)",
                    language=language,
                    task_description=task_desc,
                    code=code,
                    prompt_version=prompt_version
                )
                return {
                    "provider": "OpenAI (ChatGPT)",
                    "model": f"{model} (Demo Mode)",
                    "content": simulated_text,
                    "is_demo": True,
                    "tokens": {"prompt": 0, "completion": 0, "total": 0},
                    "error": None,
                    "notice": "Using Simulated Demo Mode: OPENAI_API_KEY is not configured in .env or settings."
                }
            return {
                "provider": "OpenAI (ChatGPT)",
                "model": model,
                "content": "",
                "is_demo": False,
                "error": "OpenAI API key is missing. Please set OPENAI_API_KEY in your .env file or UI settings."
            }

        if self.client is None:
            self.client = OpenAI(api_key=self.api_key)

        attempts = 0
        last_error = ""

        while attempts <= max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=model,
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
                    "provider": "OpenAI (ChatGPT)",
                    "model": model,
                    "content": content,
                    "is_demo": False,
                    "tokens": tokens,
                    "error": None
                }

            except AuthenticationError as e:
                return {
                    "provider": "OpenAI (ChatGPT)",
                    "model": model,
                    "content": "",
                    "is_demo": False,
                    "error": f"OpenAI Authentication Failed: Invalid API key ({str(e)}). Please verify your key at https://platform.openai.com/api-keys"
                }
            except RateLimitError as e:
                attempts += 1
                last_error = f"OpenAI Rate limit or quota exceeded: {str(e)}"
                if attempts <= max_retries:
                    time.sleep(2 * attempts)
                    continue
            except APIConnectionError as e:
                attempts += 1
                last_error = f"Network connection error contacting OpenAI: {str(e)}"
                if attempts <= max_retries:
                    time.sleep(1.5 * attempts)
                    continue
            except Exception as e:
                return {
                    "provider": "OpenAI (ChatGPT)",
                    "model": model,
                    "content": "",
                    "is_demo": False,
                    "error": f"OpenAI API Error: {str(e)}"
                }

        # If retries exhausted and demo fallback allowed
        if demo_fallback:
            simulated_text = generate_demo_review(
                provider_name="ChatGPT (OpenAI)",
                language=language,
                task_description=task_desc,
                code=code,
                prompt_version=prompt_version
            )
            return {
                "provider": "OpenAI (ChatGPT)",
                "model": f"{model} (Demo Fallback)",
                "content": simulated_text,
                "is_demo": True,
                "error": None,
                "notice": f"Live OpenAI request failed ({last_error}). Reverted to Demo Mode."
            }

        return {
            "provider": "OpenAI (ChatGPT)",
            "model": model,
            "content": "",
            "is_demo": False,
            "error": last_error
        }
