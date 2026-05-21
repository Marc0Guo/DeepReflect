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
    # Notification fields
    notify_enabled: bool | None = None
    notify_time: str | None = None
    discord_webhook_url: str | None = None
    slack_webhook_url: str | None = None
    slack_bot_token: str | None = None
    notify_channels: list[str] | None = None


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
        "port": cfg.port,
        "data_dir": cfg.data_dir,
        "notify_enabled": cfg.notify_enabled,
        "notify_time": cfg.notify_time,
        "notify_channels": [c for c in cfg.notify_channels if c in ("discord", "slack")],
        "discord_webhook_url": cfg.discord_webhook_url,
        "slack_webhook_url": cfg.slack_webhook_url,
        "slack_bot_token_set": bool(cfg.slack_bot_token),
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
    if body.notify_enabled is not None:
        cfg.notify_enabled = body.notify_enabled
    if body.notify_time is not None:
        cfg.notify_time = body.notify_time
    if body.discord_webhook_url is not None:
        cfg.discord_webhook_url = body.discord_webhook_url
    if body.slack_webhook_url is not None:
        cfg.slack_webhook_url = body.slack_webhook_url
    if body.slack_bot_token is not None:
        cfg.slack_bot_token = body.slack_bot_token
    if body.notify_channels is not None:
        cfg.notify_channels = [c for c in body.notify_channels if c in ("discord", "slack")]
    save_config(cfg)
    return {"ok": True}
