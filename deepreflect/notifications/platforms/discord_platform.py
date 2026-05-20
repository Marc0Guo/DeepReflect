"""Discord notification via webhook — supports image file attachment."""
from __future__ import annotations

import httpx


async def send(webhook_url: str, image_bytes: bytes, text: str = "") -> None:
    """POST image + optional text to a Discord Incoming Webhook."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            webhook_url,
            data={"payload_json": f'{{"content": {text!r}}}' if text else '{"content": ""}'},
            files={"file": ("deepreflect-roast.png", image_bytes, "image/png")},
        )
        resp.raise_for_status()
