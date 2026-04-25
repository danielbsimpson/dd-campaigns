from __future__ import annotations

"""Memory retrieval orchestrator.

Decides *what* goes into each LLM context request and assembles it into a
labelled string ready for injection into a prompt template.

Token budget is approximated via character count (1 token ≈ 4 chars).
Swap to tiktoken or provider-native counting in v2.
"""

import sqlite3

from .database import (
    get_active_threads,
    get_active_pcs,
    get_factions,
    get_npcs,
    get_recent_sessions,
    get_visited_locations,
)
from ..campaign.context import build_campaign_context

_CHARS_PER_TOKEN = 4


def _budget_chars(token_budget: int) -> int:
    return token_budget * _CHARS_PER_TOKEN


def _section(title: str, body: str) -> str:
    return f"## {title}\n{body.strip()}"


def _rows_to_text(rows: list[sqlite3.Row], columns: list[str], sep: str = " | ") -> str:
    lines = []
    for row in rows:
        parts = [str(row[c]) for c in columns if row[c] is not None]
        lines.append(sep.join(parts))
    return "\n".join(lines) if lines else "(none)"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def build_query_context(
    db_path: str,
    campaign_name: str,
    campaign_files: dict[str, str],
    query_text: str,
    token_budget: int = 6000,
) -> str:
    """Build context for an in-session DM query.

    Always includes: campaign lore, active threads, active PCs.
    Conditionally includes entity state based on keywords in the query.
    Fills remaining budget with recent session summaries.
    """
    sections: list[str] = []
    used = 0
    max_chars = _budget_chars(token_budget)

    # 1. Campaign lore (largest allocation: ~60% of budget)
    lore_budget = int(token_budget * 0.6)
    lore = build_campaign_context(campaign_files, token_budget=lore_budget)
    sections.append(_section("Campaign Lore", lore))
    used += len(lore)

    # 2. Active narrative threads
    threads = get_active_threads(db_path, campaign_name)
    if threads:
        lines = [f"- [{t['type'].upper()}] {t['title']}: {t['description']}" for t in threads]
        body = "\n".join(lines)
    else:
        body = "(no active threads recorded)"
    sections.append(_section("Active Threads", body))
    used += len(body)

    # 3. Active PC roster
    pcs = get_active_pcs(db_path, campaign_name)
    if pcs:
        lines = [f"- {p['character_name']} ({p['class']} level {p['level']}) — played by {p['player_name']}" for p in pcs]
        body = "\n".join(lines)
    else:
        body = "(no player characters recorded)"
    sections.append(_section("Player Characters", body))
    used += len(body)

    # 4. Conditional entity state based on query keywords
    query_lower = query_text.lower()
    remaining = max_chars - used

    npcs = get_npcs(db_path, campaign_name)
    matching_npcs = [n for n in npcs if n["name"].lower() in query_lower]
    if matching_npcs and remaining > 200:
        lines = [f"- {n['name']} ({n['role']}) — {n['disposition']}. {n['notes']}" for n in matching_npcs]
        body = "\n".join(lines)
        sections.append(_section("Relevant NPCs", body))
        used += len(body)
        remaining -= len(body)

    locations = get_visited_locations(db_path, campaign_name)
    matching_locs = [l for l in locations if l["name"].lower() in query_lower]
    if matching_locs and remaining > 200:
        lines = [f"- {l['name']}: {l['state_notes']}" for l in matching_locs]
        body = "\n".join(lines)
        sections.append(_section("Relevant Locations", body))
        used += len(body)
        remaining -= len(body)

    factions = get_factions(db_path, campaign_name)
    matching_factions = [f for f in factions if f["name"].lower() in query_lower]
    if matching_factions and remaining > 200:
        lines = [f"- {f['name']} (standing {f['standing']}): {f['notes']}" for f in matching_factions]
        body = "\n".join(lines)
        sections.append(_section("Relevant Factions", body))
        used += len(body)
        remaining -= len(body)

    # 5. Fill remaining budget with recent sessions
    if remaining > 400:
        recent = get_recent_sessions(db_path, campaign_name, n=2)
        if recent:
            lines = []
            for s in recent:
                lines.append(f"Session {s['session_number']} ({s['session_date'] or 'undated'}):")
                if s["answers"]:
                    for pair in s["answers"].split("|||"):
                        if "::" in pair:
                            _, answer = pair.split("::", 1)
                            if answer.strip():
                                lines.append(f"  {answer.strip()}")
            body = "\n".join(lines)
            body = body[: remaining - 50]
            sections.append(_section("Recent Session History", body))

    return "\n\n".join(sections)


def build_recap_context(
    db_path: str,
    campaign_name: str,
    campaign_files: dict[str, str],
    n_recent_sessions: int = 3,
    token_budget: int = 7000,
) -> str:
    """Build context for pre-session recap generation.

    Always includes: abbreviated campaign lore (README only), active PCs,
    all active threads, last N sessions, all NPCs summary, faction standings.
    """
    sections: list[str] = []
    max_chars = _budget_chars(token_budget)
    used = 0

    # 1. README only for recap (keep it short)
    readme_text = next(
        (v for k, v in campaign_files.items() if k.lower() == "readme.md"), ""
    )
    if readme_text:
        lore = _section("Campaign Overview (README)", readme_text[:_budget_chars(1500)])
        sections.append(lore)
        used += len(lore)

    # 2. Active PCs (full records)
    pcs = get_active_pcs(db_path, campaign_name)
    if pcs:
        lines = [
            f"- {p['character_name']} ({p['class']} level {p['level']}) — {p['player_name']}. {p['backstory_notes']}"
            for p in pcs
        ]
        body = "\n".join(lines)
    else:
        body = "(no player characters recorded)"
    sections.append(_section("Player Characters", body))
    used += len(body)

    # 3. All active threads (full descriptions)
    threads = get_active_threads(db_path, campaign_name)
    if threads:
        lines = [f"- [{t['type'].upper()}] **{t['title']}** (status: {t['status']})\n  {t['description']}" for t in threads]
        body = "\n".join(lines)
    else:
        body = "(no active threads)"
    sections.append(_section("Active Narrative Threads", body))
    used += len(body)

    # 4. Last N session debriefs
    recent = get_recent_sessions(db_path, campaign_name, n=n_recent_sessions)
    if recent:
        lines = []
        for s in recent:
            lines.append(f"### Session {s['session_number']} ({s['session_date'] or 'undated'})")
            if s["answers"]:
                for pair in s["answers"].split("|||"):
                    if "::" in pair:
                        key, answer = pair.split("::", 1)
                        if answer.strip():
                            lines.append(f"**{key}:** {answer.strip()}")
        body = "\n".join(lines)
        sections.append(_section("Recent Session Summaries", body))
        used += len(body)

    # 5. NPC disposition summary
    npcs = get_npcs(db_path, campaign_name)
    alive_npcs = [n for n in npcs if n["disposition"].lower() != "dead"]
    if alive_npcs:
        lines = [f"- {n['name']} ({n['role']}): {n['disposition']}" for n in alive_npcs]
        body = "\n".join(lines)
        sections.append(_section("NPC Disposition Summary", body))
        used += len(body)

    # 6. Faction standings
    factions = get_factions(db_path, campaign_name)
    if factions:
        lines = [f"- {f['name']}: standing {f['standing']}. {f['notes']}" for f in factions]
        body = "\n".join(lines)
        sections.append(_section("Faction Standings", body))

    # Trim to budget (rough)
    result = "\n\n".join(sections)
    if len(result) > max_chars:
        result = result[:max_chars] + "\n\n[Context truncated to fit token budget]"
    return result


def build_debrief_context(
    db_path: str,
    campaign_name: str,
) -> str:
    """Lightweight context for the debrief review pass.

    Returns active thread titles, NPC names, and location names so the UI
    can suggest linkages after the DM saves their answers.
    """
    parts: list[str] = []

    threads = get_active_threads(db_path, campaign_name)
    if threads:
        parts.append("Active threads: " + ", ".join(t["title"] for t in threads))

    npcs = get_npcs(db_path, campaign_name)
    if npcs:
        parts.append("Known NPCs: " + ", ".join(n["name"] for n in npcs))

    locations = get_visited_locations(db_path, campaign_name)
    if locations:
        parts.append("Known locations: " + ", ".join(l["name"] for l in locations))

    return "\n".join(parts)
