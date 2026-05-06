"""Coach agent: generates intervention messages when users repeat questions."""
from __future__ import annotations

_TONE_TEMPLATES = {
    "strict": (
        "You have asked about **{concepts}** {count} times. "
        "This is a knowledge gap. Before asking again, write your current understanding. "
        "Then re-read your previous answers."
    ),
    "friendly": (
        "Hey! Looks like **{concepts}** keeps coming up — you've asked about it {count} times. "
        "That's totally fine, but maybe try explaining it in your own words first? "
        "It'll stick better that way."
    ),
    "funny": (
        "Alert! Your brain has sent {count} help requests about **{concepts}**. "
        "The AI is starting to wonder if you two are just pen pals now. "
        "Try explaining it yourself first — I believe in you."
    ),
}


def build_intervention_message(
    concepts: list[str],
    ask_count: int,
    tone: str = "friendly",
) -> str:
    template = _TONE_TEMPLATES.get(tone, _TONE_TEMPLATES["friendly"])
    return template.format(
        concepts=", ".join(concepts),
        count=ask_count,
    )


def format_hook_output(message: str) -> str:
    """Format for Claude Code hook stdout — printed as a pre-tool warning."""
    return f"\n[DeepReflect] {message}\n"
