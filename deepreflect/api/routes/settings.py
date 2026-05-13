from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from deepreflect.config import load_config, save_config

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    intervention_tone: str | None = None
    repeat_threshold: int | None = None


@router.get("")
async def get_settings():
    cfg = load_config()
    key = cfg.llm_api_key
    masked = (key[:6] + "..." + key[-3:]) if len(key) > 9 else ("***" if key else "")
    return {
        "llm_provider": cfg.llm_provider,
        "llm_api_key_masked": masked,
        "llm_api_key_set": bool(key),
        "llm_model": cfg.llm_model,
        "llm_base_url": cfg.llm_base_url,
        "intervention_tone": cfg.intervention_tone,
        "repeat_threshold": cfg.repeat_threshold,
        "port": cfg.port,
        "data_dir": cfg.data_dir,
    }


@router.post("")
async def update_settings(body: SettingsUpdate):
    cfg = load_config()
    if body.llm_provider is not None:
        cfg.llm_provider = body.llm_provider
    if body.llm_api_key is not None:
        cfg.llm_api_key = body.llm_api_key
    if body.llm_model is not None:
        cfg.llm_model = body.llm_model
    if body.llm_base_url is not None:
        cfg.llm_base_url = body.llm_base_url
    if body.intervention_tone is not None:
        cfg.intervention_tone = body.intervention_tone
    if body.repeat_threshold is not None:
        cfg.repeat_threshold = body.repeat_threshold
    save_config(cfg)
    return {"ok": True}
