"""Anthropic / Claude API Provider for C4 Code Review Assistant."""

from __future__ import annotations
import os
import time
from typing import Dict, Any, Optional
from modules.demo_generator import generate_demo_review

try:
    import anthropic
    from anthropic import Anthropic, AuthenticationError, RateLimitError, APIConnectionError, APIStatusError
except ImportError:
    anthropic = None
    Anthropic = None
    AuthenticationError = RateLimitError = APIConnectionError = APIStatusError = Exception


class ClaudeProvider:
    """Manages Claude API integration using the official Anthropic Python SDK."""

    AVAILABLE_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-haiku-20240307"
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.client = None
        if self.is_configured() and Anthropic is not None:
            try:
                self.client = Anthropic(api_key=self.api_key)
            except Exception:
                self.client = None

    def is_configured(self) -> bool:
        """Returns True if a real API key is present and not a dummy placeholder."""
        if not self.api_key:
            return False
        if any(placeholder in self.api_key.lower() for placeholder in ["your_", "placeholder", "key_here", "sk-ant-xxx"]):
            return False
        return len(self.api_key) > 10

    def review_code(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.2,
        max_retries: int = 2,
        demo_fallback: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submits code review prompt to Anthropic Claude and returns structured result."""
        context = context or {}
        language = context.get("language", "Python")
        task_desc = context.get("task_description", "")
        code = context.get("code", "")
        prompt_version = context.get("prompt_version", "v3")

        # Fallback to demo mode if not configured
        if not self.is_configured():
            if demo_fallback:
                simulated_text = generate_demo_review(
                    provider_name="Claude (Anthropic)",
                    language=language,
                    task_description=task_desc,
                    code=code,
                    prompt_version=prompt_version
                )
                return {
                    "provider": "Claude (Anthropic)",
                    "model": f"{model} (Demo Mode)",
                    "content": simulated_text,
                    "is_demo": True,
                    "tokens": {"prompt": 0, "completion": 0, "total": 0},
                    "error": None,
                    "notice": "Using Simulated Demo Mode: ANTHROPIC_API_KEY is not configured in .env or settings."
                }
            return {
                "provider": "Claude (Anthropic)",
                "model": model,
                "content": "",
                "is_demo": False,
                "error": "Anthropic API key is missing. Please set ANTHROPIC_API_KEY in your .env file or UI settings."
            }

        if self.client is None:
            self.client = Anthropic(api_key=self.api_key)

        attempts = 0
        last_error = ""

        while attempts <= max_retries:
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=2500,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature
                )

                # Extract text content from Anthropic response blocks
                content_parts = []
                for block in response.content:
                    if hasattr(block, "text"):
                        content_parts.append(block.text)
                    elif isinstance(block, dict) and "text" in block:
                        content_parts.append(block["text"])

                content = "\n".join(content_parts)
                usage = getattr(response, "usage", None)
                tokens = {
                    "prompt": getattr(usage, "input_tokens", 0) if usage else 0,
                    "completion": getattr(usage, "output_tokens", 0) if usage else 0,
                    "total": (getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0)) if usage else 0,
                }

                return {
                    "provider": "Claude (Anthropic)",
                    "model": model,
                    "content": content,
                    "is_demo": False,
                    "tokens": tokens,
                    "error": None
                }

            except AuthenticationError as e:
                return {
                    "provider": "Claude (Anthropic)",
                    "model": model,
                    "content": "",
                    "is_demo": False,
                    "error": f"Anthropic Authentication Failed: Invalid API key ({str(e)}). Check your key at https://console.anthropic.com/"
                }
            except RateLimitError as e:
                attempts += 1
                last_error = f"Claude Rate limit reached: {str(e)}"
                if attempts <= max_retries:
                    time.sleep(2 * attempts)
                    continue
            except APIConnectionError as e:
                attempts += 1
                last_error = f"Network connection error contacting Anthropic: {str(e)}"
                if attempts <= max_retries:
                    time.sleep(1.5 * attempts)
                    continue
            except Exception as e:
                return {
                    "provider": "Claude (Anthropic)",
                    "model": model,
                    "content": "",
                    "is_demo": False,
                    "error": f"Anthropic API Error: {str(e)}"
                }

        # If retries exhausted and demo fallback allowed
        if demo_fallback:
            simulated_text = generate_demo_review(
                provider_name="Claude (Anthropic)",
                language=language,
                task_description=task_desc,
                code=code,
                prompt_version=prompt_version
            )
            return {
                "provider": "Claude (Anthropic)",
                "model": f"{model} (Demo Fallback)",
                "content": simulated_text,
                "is_demo": True,
                "error": None,
                "notice": f"Live Claude request failed ({last_error}). Reverted to Demo Mode."
            }

        return {
            "provider": "Claude (Anthropic)",
            "model": model,
            "content": "",
            "is_demo": False,
            "error": last_error
        }
