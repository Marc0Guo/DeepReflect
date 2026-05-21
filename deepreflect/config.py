from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel

_CONFIG_DIR = Path.home() / ".deepreflect"
_CONFIG_FILE = _CONFIG_DIR / "config.json"
_DATA_DIR = _CONFIG_DIR / "data"


class Config(BaseModel):
    # anthropic | openai | ollama | openrouter
    llm_provider: str = os.getenv("DEEPREFLECT_LLM_PROVIDER", "openai")
    llm_api_key: str = os.getenv("DEEPREFLECT_LLM_API_KEY", "")
    llm_model: str = os.getenv("DEEPREFLECT_LLM_MODEL", "gpt-4o-mini")
    llm_base_url: str = os.getenv("DEEPREFLECT_LLM_BASE_URL", "")  # custom endpoint override
    port: int = 7733
    repeat_threshold: int = 3  # warn after N repeats
    intervention_tone: str = "friendly"  # strict | friendly | funny
    data_dir: str = str(_DATA_DIR)

    # ── Notification settings ─────────────────────────────────────────────────
    notify_enabled: bool = False
    notify_time: str = "21:00"          # HH:MM local time
    discord_webhook_url: str = ""
    slack_webhook_url: str = ""
    slack_bot_token: str = ""           # optional; enables image upload
    imessage_recipient: str = ""        # phone number or Apple ID email
    wechat_recipient: str = ""          # exact contact display name in WeChat desktop
    notify_channels: list[str] = []     # ["discord","slack","imessage","wechat"]

    @property
    def db_path(self) -> Path:
        return Path(self.data_dir) / "deepreflect.db"

    @property
    def summaries_dir(self) -> Path:
        return Path(self.data_dir) / "summaries"


def load_config() -> Config:
    if _CONFIG_FILE.exists():
        return Config(**json.loads(_CONFIG_FILE.read_text()))
    return Config()


def save_config(cfg: Config) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(cfg.model_dump_json(indent=2))


def ensure_dirs(cfg: Config) -> None:
    Path(cfg.data_dir).mkdir(parents=True, exist_ok=True)
    cfg.summaries_dir.mkdir(parents=True, exist_ok=True)


def llm_is_ready(cfg: Config) -> bool:
    """Ollama runs locally and does not need an API key."""
    return cfg.llm_provider == "ollama" or bool(cfg.llm_api_key)
