from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.llm_config_manager import LLMConfigManager


@pytest.mark.asyncio
async def test_llm_config_manager_multi_ai_switching():
    """
    Tests:
    1. Managing multiple API keys (Gemini, OpenAI, Claude, Groq, DeepSeek).
    2. Disabling a key keeps it preserved for future reenabling.
    3. Switching active AI model dynamically.
    """
    LLMConfigManager.initialize_defaults()

    # 1. Add key for OpenAI
    LLMConfigManager.update_provider("openai", api_key="sk-test-openai-key-12345", is_enabled=True)
    openai_cfg = LLMConfigManager._providers["openai"]
    assert openai_cfg.is_enabled
    assert openai_cfg.api_key == "sk-test-openai-key-12345"

    # 2. Switch active to OpenAI
    active_id = LLMConfigManager.set_active_provider("openai")
    assert active_id == "openai"
    assert LLMConfigManager.get_active_provider_config().id == "openai"

    # 3. Disable OpenAI: Key should NOT be erased!
    LLMConfigManager.update_provider("openai", is_enabled=False)
    assert not LLMConfigManager._providers["openai"].is_enabled
    assert LLMConfigManager._providers["openai"].api_key == "sk-test-openai-key-12345"  # Preserved!

    # 4. Re-enable OpenAI without needing to re-enter the key
    LLMConfigManager.update_provider("openai", is_enabled=True)
    assert LLMConfigManager._providers["openai"].is_enabled


@pytest.mark.asyncio
async def test_ai_settings_api_endpoints(client: AsyncClient):
    """
    Integration test for /api/v1/ai endpoints:
    - GET /api/v1/ai/providers
    - POST /api/v1/ai/providers/update
    - POST /api/v1/ai/providers/switch
    """
    # 1. List providers
    res = await client.get("/api/v1/ai/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 5
    ids = [p["id"] for p in providers]
    assert "gemini" in ids
    assert "openai" in ids
    assert "claude" in ids
    assert "groq" in ids
    assert "deepseek" in ids

    # 2. Update Groq key
    up_res = await client.post(
        "/api/v1/ai/providers/update",
        json={"provider_id": "groq", "api_key": "gsk_testgroqkey98765", "is_enabled": True}
    )
    assert up_res.status_code == 200
    assert up_res.json()["is_enabled"]

    # 3. Switch active AI to Groq
    sw_res = await client.post(
        "/api/v1/ai/providers/switch",
        json={"provider_id": "groq"}
    )
    assert sw_res.status_code == 200
    assert sw_res.json()["active_provider_id"] == "groq"

    # 4. Disable Groq (without key loss)
    dis_res = await client.post(
        "/api/v1/ai/providers/update",
        json={"provider_id": "groq", "is_enabled": False}
    )
    assert dis_res.status_code == 200
    assert not dis_res.json()["is_enabled"]
