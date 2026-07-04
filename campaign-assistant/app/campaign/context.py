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


def build_recap_context(
    files: dict[str, str],
    sessions: list,
    token_budget: int = 8000,
) -> str:
    """Build a combined context block for pre-session recap generation.

    Includes an abbreviated campaign lore section (README + .txt files only)
    followed by recent session debrief answers, newest first.  Characters and
    creatures files are omitted here because the recap prompt focuses on
    narrative continuity rather than reference lookup.

    Args:
        files:        Dict of filename → text from ``loader.load_campaign()``.
        sessions:     Rows returned by ``database.get_recent_sessions()``.
                      Each row must have ``session_number``, ``session_date``,
                      and ``answers`` (GROUP_CONCAT of ``key::text`` pairs
                      separated by ``|||``).
        token_budget: Approximate token limit for the entire block.

    Returns:
        A formatted string ready for injection into the recap prompt.
    """
    max_chars = _budget_chars(token_budget)
    sections: list[str] = []
    used = 0

    # --- Abbreviated campaign lore: README + .txt files only ---
    lore_parts: list[str] = []
    for name in files:
        name_lower = name.lower()
        if name_lower == "readme.md" or name_lower.endswith(".txt"):
            remaining = max_chars - used - sum(len(p) for p in lore_parts)
            if remaining > 0:
                truncated = _truncate(files[name], remaining, name)
                lore_parts.append(f"### {name}\n{truncated}")

    if lore_parts:
        block = "\n\n".join(lore_parts)
        sections.append(f"## Campaign Lore\n{block}")
        used += len(sections[-1])

    # --- Session debrief history (newest first) ---
    history_parts: list[str] = []
    for row in sessions:
        remaining = max_chars - used
        if remaining <= 0:
            break

        session_num = row["session_number"]
        session_date = row["session_date"] or "unknown date"
        raw_answers: str = row["answers"] or ""

        answer_lines: list[str] = []
        if raw_answers:
            for pair in raw_answers.split("|||"):
                if "::" in pair:
                    key, _, answer_text = pair.partition("::")
                    if answer_text.strip():
                        answer_lines.append(f"**{key}**: {answer_text.strip()}")

        if not answer_lines:
            continue

        part = f"### Session {session_num} ({session_date})\n" + "\n".join(answer_lines)
        truncated = _truncate(part, remaining, f"Session {session_num}")
        history_parts.append(truncated)
        used += len(truncated)

    if history_parts:
        sections.append("## Session History\n" + "\n\n".join(history_parts))

    return "\n\n".join(sections)
