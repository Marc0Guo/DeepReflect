"""Plain-text extraction from Claude/Cursor message payloads."""


def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_result":
                    for sub in block.get("content", []):
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            parts.append(sub.get("text", ""))
        return "\n".join(p for p in parts if p).strip()
    return str(content) if content is not None else ""
