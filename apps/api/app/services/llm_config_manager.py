from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ProviderConfig(BaseModel):
    id: str  # e.g. "gemini", "openai", "claude", "groq", "deepseek"
    name: str  # Display name e.g. "Google Gemini", "OpenAI GPT-4o"
    api_key: Optional[str] = None
    model_name: str
    base_url: Optional[str] = None
    is_enabled: bool = False
    is_active: bool = False  # Currently selected for chatbot responses


class LLMConfigManager:
    """
    Manages multi-provider AI keys and states.
    Allows enabling, disabling (retaining keys securely), switching active models,
    and on-the-fly execution routing.
    """

    _providers: Dict[str, ProviderConfig] = {}
    _active_provider_id: str = "gemini"

    @classmethod
    def initialize_defaults(cls, gemini_key: Optional[str] = None, openai_key: Optional[str] = None) -> None:
        cls._providers = {
            "gemini": ProviderConfig(
                id="gemini",
                name="Google Gemini",
                api_key=gemini_key or os.environ.get("GEMINI_API_KEY"),
                model_name="gemini-3.5-flash-lite",
                is_enabled=bool(gemini_key or os.environ.get("GEMINI_API_KEY")),
                is_active=True
            ),
            "openai": ProviderConfig(
                id="openai",
                name="OpenAI (GPT-4o / GPT-4o-mini)",
                api_key=openai_key or os.environ.get("OPENAI_API_KEY"),
                model_name="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                is_enabled=bool(openai_key or os.environ.get("OPENAI_API_KEY")),
                is_active=False
            ),
            "claude": ProviderConfig(
                id="claude",
                name="Anthropic Claude",
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
                model_name="claude-3-5-sonnet-20241022",
                base_url="https://api.anthropic.com/v1",
                is_enabled=bool(os.environ.get("ANTHROPIC_API_KEY")),
                is_active=False
            ),
            "groq": ProviderConfig(
                id="groq",
                name="Groq (Llama 3 / Mixtral)",
                api_key=os.environ.get("GROQ_API_KEY"),
                model_name="llama-3.3-70b-versatile",
                base_url="https://api.groq.com/openai/v1",
                is_enabled=bool(os.environ.get("GROQ_API_KEY")),
                is_active=False
            ),
            "deepseek": ProviderConfig(
                id="deepseek",
                name="DeepSeek",
                api_key=os.environ.get("DEEPSEEK_API_KEY"),
                model_name="deepseek-chat",
                base_url="https://api.deepseek.com/v1",
                is_enabled=bool(os.environ.get("DEEPSEEK_API_KEY")),
                is_active=False
            )
        }

        # Select first enabled provider as active if gemini is not enabled
        if not cls._providers["gemini"].is_enabled:
            for p in cls._providers.values():
                if p.is_enabled:
                    cls.set_active_provider(p.id)
                    break

    @classmethod
    def list_providers(cls) -> List[Dict[str, Any]]:
        if not cls._providers:
            cls.initialize_defaults()

        models_map = {
            "gemini": ["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
            "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            "claude": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
            "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            "deepseek": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
        }
        results = []
        for p in cls._providers.values():
            # Mask API key for security (never expose full key in public GET)
            masked_key = None
            if p.api_key:
                masked_key = p.api_key[:4] + "..." + p.api_key[-4:] if len(p.api_key) > 8 else "***"

            results.append({
                "id": p.id,
                "provider": p.id,
                "name": p.name,
                "has_key": bool(p.api_key),
                "masked_key": masked_key,
                "model_name": p.model_name,
                "model": p.model_name,
                "available_models": models_map.get(p.id, [p.model_name]),
                "is_enabled": p.is_enabled,
                "is_active": p.id == cls._active_provider_id
            })
        return results

    @classmethod
    def update_provider(
        cls,
        provider_id: str,
        api_key: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        model_name: Optional[str] = None
    ) -> ProviderConfig:
        if not cls._providers:
            cls.initialize_defaults()

        if provider_id not in cls._providers:
            raise KeyError(f"Unknown provider '{provider_id}'")

        cfg = cls._providers[provider_id]
        if api_key is not None and api_key.strip():
            cfg.api_key = api_key.strip()
            # If user supplies key, automatically enable unless explicitly told otherwise
            if is_enabled is None:
                cfg.is_enabled = True

        if is_enabled is not None:
            cfg.is_enabled = is_enabled

        if model_name is not None and model_name.strip():
            cfg.model_name = model_name.strip()

        # If currently active provider was disabled, switch to another enabled one
        if not cfg.is_enabled and cls._active_provider_id == provider_id:
            for pid, p in cls._providers.items():
                if p.is_enabled and p.api_key:
                    cls._active_provider_id = pid
                    break

        return cfg

    @classmethod
    def set_active_provider(cls, provider_id: str) -> str:
        if not cls._providers:
            cls.initialize_defaults()

        if provider_id not in cls._providers:
            raise KeyError(f"Unknown provider '{provider_id}'")

        cfg = cls._providers[provider_id]
        if not cfg.is_enabled:
            raise ValueError(f"Provider '{cfg.name}' is currently disabled. Enable it before setting as active.")
        if not cfg.api_key:
            raise ValueError(f"Provider '{cfg.name}' has no API key configured.")

        cls._active_provider_id = provider_id
        for p in cls._providers.values():
            p.is_active = (p.id == provider_id)

        return cls._active_provider_id

    @classmethod
    def get_active_provider_config(cls) -> ProviderConfig:
        if not cls._providers:
            cls.initialize_defaults()
        return cls._providers.get(cls._active_provider_id, cls._providers["gemini"])
