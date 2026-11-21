from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from app.config import settings


class LLMMessage(BaseModel):
    role: str  # system | user | assistant
    content: str


class LLMResponse(BaseModel):
    content: str
    tokens_used: int = 0
    model: str = "mock"
    raw_response: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self, messages: List[LLMMessage], temperature: float = 0.2, max_tokens: int = 600
    ) -> LLMResponse:
        """Generate response from language model."""
        pass


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock provider for unit tests, offline development,
    and adversarial red-team leak-guard verification.
    """

    def __init__(self, force_leak: bool = False, leak_content: str = ""):
        self.force_leak = force_leak
        self.leak_content = leak_content

    async def generate_response(
        self, messages: List[LLMMessage], temperature: float = 0.2, max_tokens: int = 600
    ) -> LLMResponse:
        # If test suite triggers forced leak, output leaky response to test leak-guard interception
        if self.force_leak:
            return LLMResponse(
                content=self.leak_content
                or "Here is the exact code:\n```python\ndef two_sum(nums, target):\n    lookup = {}\n    for i, num in enumerate(nums):\n        diff = target - num\n        if diff in lookup:\n            return [lookup[diff], i]\n        lookup[num] = i\n    return []\n```",
                tokens_used=45,
                model="mock-leaky",
            )

        # Inspect last user prompt
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "").lower()
        sys_msg = next((m.content for m in messages if m.role == "system"), "")

        # Detect rung from system prompt or message
        if "rung: guide" in sys_msg.lower() or "guide" in user_msg:
            content = "What core data structure allows checking whether a complement element exists in O(1) average time? Can you identify what needs to be stored as the key versus value?"
        elif "rung: hint" in sys_msg.lower() or "hint" in user_msg:
            content = "Consider keeping track of elements you have already seen in a hash map as you iterate through the list once. What would you look up on each step?"
        elif "rung: help" in sys_msg.lower() or "help" in user_msg:
            content = "Let's explore a similar concept: finding two words that concatenate to a target string. Instead of checking every pair with nested loops (O(n²)), you can store seen prefixes in a set and check if the remaining suffix is present in O(1). How could you adapt this complement lookup to numbers?"
        elif "rung: critical_hint" in sys_msg.lower() or "critical_hint" in user_msg:
            content = "Next single step: initialize an empty dictionary `seen = {}`. When visiting number `num` at index `i`, compute `diff = target - num`. Write an `if diff in seen:` condition. What should you return if true?"
        else:
            content = "Let's break this down together. What initial approach came to mind when you first read the problem statement?"

        return LLMResponse(content=content, tokens_used=60, model="mock-deterministic")


class GeminiLLMProvider(LLMProvider):
    """Google Gemini adapter using the official google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = "gemini-3.5-flash-lite"

    async def generate_response(
        self, messages: List[LLMMessage], temperature: float = 0.2, max_tokens: int = 600
    ) -> LLMResponse:
        if not self.api_key:
            fallback = MockLLMProvider()
            return await fallback.generate_response(messages, temperature, max_tokens)

        import asyncio

        from google import genai

        # Format system prompt and contents
        system_instruction = "\n\n".join(m.content for m in messages if m.role == "system")
        contents = []
        for m in messages:
            if m.role == "user":
                contents.append(f"User: {m.content}")
            elif m.role == "assistant":
                contents.append(f"Assistant: {m.content}")

        combined_prompt = "\n".join(contents)
        client = genai.Client(api_key=self.api_key)

        def _call_api():
            config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if system_instruction:
                config["system_instruction"] = system_instruction
            return client.models.generate_content(
                model=self.model_name,
                contents=combined_prompt,
                config=config,
            )

        resp = await asyncio.to_thread(_call_api)
        text = resp.text or ""

        return LLMResponse(
            content=text,
            tokens_used=getattr(resp, "usage_metadata", {}).total_token_count if hasattr(resp, "usage_metadata") and resp.usage_metadata else 50,
            model=self.model_name,
            raw_response=None,
        )


class OpenAILLMProvider(LLMProvider):
    """OpenAI / OpenAI-compatible API adapter (supports OpenAI, Groq, DeepSeek)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.model_name = model_name

    async def generate_response(
        self, messages: List[LLMMessage], temperature: float = 0.2, max_tokens: int = 600
    ) -> LLMResponse:
        if not self.api_key:
            fallback = MockLLMProvider()
            return await fallback.generate_response(messages, temperature, max_tokens)

        formatted_msgs = [{"role": m.role, "content": m.content} for m in messages]
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise Exception(f"AI API error ({resp.status_code}): {resp.text}")

            data = resp.json()
            choice = data["choices"][0]
            return LLMResponse(
                content=choice["message"]["content"],
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                model=self.model_name,
                raw_response=data,
            )


def get_llm_provider() -> LLMProvider:
    import os

    from app.services.llm_config_manager import LLMConfigManager

    if settings.ENVIRONMENT == "test" or os.environ.get("ENVIRONMENT") == "test":
        return MockLLMProvider()

    active_cfg = LLMConfigManager.get_active_provider_config()
    if not active_cfg.is_enabled or not active_cfg.api_key:
        return MockLLMProvider()

    if active_cfg.id == "gemini":
        prov = GeminiLLMProvider(api_key=active_cfg.api_key)
        prov.model_name = active_cfg.model_name
        return prov
    else:
        # OpenAI, Claude (via compatible proxy/endpoint), Groq, DeepSeek
        return OpenAILLMProvider(
            api_key=active_cfg.api_key,
            base_url=active_cfg.base_url or "https://api.openai.com/v1",
            model_name=active_cfg.model_name
        )
