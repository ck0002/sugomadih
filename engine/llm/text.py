"""Cleanup for LLM-written story text."""


def clean_story(value: object, limit: int) -> str:
    """Collapse whitespace, cap length, and if the model got cut off mid-sentence end at the last full one.
    Returns "" for non-strings / empty text (callers pick their own fallback)."""
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split())[:limit]
    if text and text[-1] not in ".!?\"'":
        end = max(text.rfind(p) for p in ".!?")
        text = text[: end + 1] if end > 0 else text + "..."
    return text
