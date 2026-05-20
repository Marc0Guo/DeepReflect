"""Slack notification via Incoming Webhook (text) + optional Files API (image)."""
from __future__ import annotations

import json

import httpx


async def send(
    webhook_url: str,
    bot_token: str,
    image_bytes: bytes,
    headline: str = "Your Daily DeepRoast 🔥",
) -> None:
    """Post a notification to Slack.

    Without bot_token: sends a text-only message via Incoming Webhook.
    With bot_token: uploads the image to Slack first, then posts a message with it.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        if bot_token:
            # Upload image and get a public permalink
            upload_resp = await client.post(
                "https://slack.com/api/files.upload",
                headers={"Authorization": f"Bearer {bot_token}"},
                data={"filename": "deepreflect-roast.png", "initial_comment": headline},
                files={"file": ("deepreflect-roast.png", image_bytes, "image/png")},
            )
            upload_resp.raise_for_status()
            data = upload_resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Slack file upload failed: {data.get('error')}")
            # Also post a webhook message so it appears in the correct channel
            img_url = data.get("file", {}).get("permalink", "")
            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*{headline}*"}},
                {"type": "image", "image_url": img_url, "alt_text": "DeepReflect Roast"},
            ] if img_url else [
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*{headline}*"}},
            ]
            body = json.dumps({"blocks": blocks})
        else:
            # Text-only fallback
            body = json.dumps({
                "text": f"*{headline}*\nOpen DeepReflect to view your daily roast.",
            })

        resp = await client.post(
            webhook_url,
            content=body,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
