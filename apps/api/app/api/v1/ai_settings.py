from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.llm_config_manager import LLMConfigManager

router = APIRouter()


class ProviderStatusItem(BaseModel):
    id: str
    name: str
    has_key: bool
    masked_key: Optional[str]
    model_name: str
    is_enabled: bool
    is_active: bool


class UpdateKeyRequest(BaseModel):
    provider_id: str
    api_key: Optional[str] = None
    is_enabled: Optional[bool] = None
    model_name: Optional[str] = None


class SetActiveRequest(BaseModel):
    provider_id: str


@router.get("/providers", response_model=List[ProviderStatusItem])
async def list_available_providers():
    """
    Lists all AI engines, their enable/disable status, masked key indicators,
    and which AI is currently driving ThinkFree's Socratic chatbot.
    """
    return LLMConfigManager.list_providers()


@router.post("/providers/update")
async def update_provider_key(data: UpdateKeyRequest):
    """
    Add, update, enable, or disable an AI provider key.
    Note: Disabling does NOT delete the key, preserving it for effortless reenabling.
    """
    try:
        updated = LLMConfigManager.update_provider(
            provider_id=data.provider_id,
            api_key=data.api_key,
            is_enabled=data.is_enabled,
            model_name=data.model_name
        )
        return {
            "status": "success",
            "provider_id": updated.id,
            "is_enabled": updated.is_enabled,
            "message": f"{updated.name} configuration updated."
        }
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/providers/switch")
async def switch_active_ai(data: SetActiveRequest):
    """
    Switch the active chatbot model to any enabled provider with a configured key.
    """
    try:
        active_id = LLMConfigManager.set_active_provider(data.provider_id)
        return {
            "status": "switched",
            "active_provider_id": active_id,
            "message": f"Active Socratic AI switched to {active_id}."
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
