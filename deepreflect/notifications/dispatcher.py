"""Orchestrate daily notification: generate roast → PNG → send to all channels."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from deepreflect.config import Config
from deepreflect.analysis.llm_client import LLMClient
from deepreflect.agents.roast_generator import generate_roast_html
from deepreflect.memory.db import get_session
from deepreflect.notifications.image_gen import html_to_png
from deepreflect.notifications import platforms as _p

log = logging.getLogger(__name__)

# Track last dispatch time (in-process only; resets on server restart)
_last_sent: datetime | None = None


def get_last_sent() -> datetime | None:
    return _last_sent


async def dispatch_notification(cfg: Config) -> dict[str, str]:
    """Generate a fresh roast, screenshot it, and send to all configured channels.

    Returns a dict mapping channel → "ok" | error message.
    """
    global _last_sent

    if not cfg.notify_channels:
        return {}

    # ── 1. Generate roast HTML ────────────────────────────────────────────────
    log.info("Notification: generating roast HTML…")
    llm = LLMClient.from_config(cfg)
    with get_session(cfg.db_path) as session:
        html_path = await generate_roast_html(session, llm, cfg.summaries_dir)

    # ── 2. Screenshot → PNG bytes ─────────────────────────────────────────────
    log.info("Notification: rendering PNG from %s…", html_path.name)
    image_error: str | None = None
    try:
        image_bytes = await html_to_png(html_path)
    except RuntimeError as exc:
        image_error = str(exc)
        log.error("Image generation failed: %s", exc)
        image_bytes = None
    except Exception as exc:
        image_error = str(exc)
        log.error("Image generation failed: %s", exc)
        image_bytes = None

    # ── 3. Dispatch to each channel ───────────────────────────────────────────
    results: dict[str, str] = {}

    for channel in cfg.notify_channels:
        if channel not in ("discord", "slack"):
            continue
        try:
            if channel == "discord":
                if not cfg.discord_webhook_url:
                    results[channel] = "error: webhook URL not configured"
                    continue
                if image_bytes is None:
                    results[channel] = f"error: {image_error or 'image generation failed'}"
                    continue
                from deepreflect.notifications.platforms import discord_platform
                await discord_platform.send(cfg.discord_webhook_url, image_bytes)

            elif channel == "slack":
                if not cfg.slack_webhook_url:
                    results[channel] = "error: webhook URL not configured"
                    continue
                from deepreflect.notifications.platforms import slack_platform
                await slack_platform.send(
                    cfg.slack_webhook_url,
                    cfg.slack_bot_token,
                    image_bytes or b"",
                )

            else:
                results[channel] = f"error: unknown channel '{channel}'"
                continue

            results[channel] = "ok"
            log.info("Notification sent via %s", channel)

        except Exception as exc:
            log.error("Failed to send via %s: %s", channel, exc)
            results[channel] = f"error: {exc}"

    _last_sent = datetime.now()
    return results
