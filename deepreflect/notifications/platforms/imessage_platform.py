"""iMessage notification via macOS AppleScript (Messages.app). macOS only."""
from __future__ import annotations

import asyncio
import platform
import sys
from pathlib import Path


async def send(recipient: str, image_path: Path | None = None, text: str = "") -> None:
    """Send a message (and optionally an image) via iMessage on macOS.

    recipient: phone number (e.g. '+15551234567') or Apple ID email.
    image_path: path to the PNG to attach (sent as a file attachment).
    text: optional caption; shown above the image.
    """
    if platform.system() != "Darwin":
        raise RuntimeError("iMessage is only available on macOS.")

    recipient_safe = recipient.replace('"', '\\"')

    parts: list[str] = []
    if text:
        text_safe = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        parts.append(
            f'''tell application "Messages"
    set t to first service whose service type = iMessage
    set b to buddy "{recipient_safe}" of t
    send "{text_safe}" to b
end tell'''
        )

    if image_path is not None and image_path.exists():
        posix = str(image_path.resolve()).replace('"', '\\"')
        parts.append(
            f'''tell application "Messages"
    set t to first service whose service type = iMessage
    set b to buddy "{recipient_safe}" of t
    send (POSIX file "{posix}") to b
end tell'''
        )

    if not parts:
        return

    for script in parts:
        proc = await asyncio.create_subprocess_exec(
            "/usr/bin/osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"osascript error: {stderr.decode().strip()}")
