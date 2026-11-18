"""Helpers for working with message text."""


def normalize_text(text: str) -> str:
    """Lowercase the text and collapse repeated whitespace into single spaces."""
    words = text.lower().split()
    return " ".join(words)
