from __future__ import annotations

# Rough character-to-token ratio used for budget estimation (v1).
# Swap to tiktoken or provider-native counting in v2.
_CHARS_PER_TOKEN = 4


def _budget_chars(token_budget: int) -> int:
    return token_budget * _CHARS_PER_TOKEN


def _truncate(text: str, max_chars: int, label: str) -> str:
    """Truncate text to max_chars, appending a notice if cut."""
    if len(text) <= max_chars:
        return text
    cutoff = max(0, max_chars - 60)
    return text[:cutoff] + f"\n\n[{label} truncated to fit token budget]"


def build_campaign_context(
    files: dict[str, str],
    token_budget: int = 6000,
) -> str:
    """Render all campaign files into a single labelled context block.

    Files are included in a stable order: README first, then the .txt
    narrative file, then characters.md, then creatures.md, then any
    remaining files alphabetically. Each section is truncated if the
    cumulative character count approaches the budget.

    Args:
        files:        Dict of filename → text from ``loader.load_campaign()``.
        token_budget: Approximate token limit for the entire block.

    Returns:
        A formatted string ready for injection into a prompt.
    """
    if not files:
        return ""

    max_chars = _budget_chars(token_budget)

    # Determine insertion order
    order = []
    for priority in ("readme.md", ):
        for name in files:
            if name.lower() == priority:
                order.append(name)
    for name in files:
        if name.lower().endswith(".txt") and name not in order:
            order.append(name)
    for priority in ("characters.md", "creatures.md"):
        for name in files:
            if name.lower() == priority and name not in order:
                order.append(name)
    for name in sorted(files):
        if name not in order:
            order.append(name)

    sections: list[str] = []
    used = 0

    for name in order:
        text = files[name]
        remaining = max_chars - used
        if remaining <= 0:
            sections.append(f"## {name}\n[Omitted — token budget exhausted]")
            continue
        truncated = _truncate(text, remaining, name)
        sections.append(f"## {name}\n{truncated}")
        used += len(truncated)

    return "\n\n".join(sections)
