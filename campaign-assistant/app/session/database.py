from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Generator


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def _cursor(db_path: str) -> Generator[sqlite3.Cursor, None, None]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema creation & migrations
# ---------------------------------------------------------------------------

_SCHEMA_VERSION = 1

_DDL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name  TEXT    NOT NULL,
    session_number INTEGER NOT NULL,
    session_date   TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS debrief_answers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_key TEXT    NOT NULL,
    answer_text  TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS recaps (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    recap_text   TEXT    NOT NULL,
    generated_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Entity state: NPCs
CREATE TABLE IF NOT EXISTS npcs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name      TEXT    NOT NULL,
    name               TEXT    NOT NULL,
    role               TEXT    NOT NULL DEFAULT '',
    disposition        TEXT    NOT NULL DEFAULT 'unknown',
    last_seen_session  INTEGER,
    notes              TEXT    NOT NULL DEFAULT '',
    updated_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(campaign_name, name)
);

-- Entity state: Locations
CREATE TABLE IF NOT EXISTS locations (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name      TEXT    NOT NULL,
    name               TEXT    NOT NULL,
    visited            INTEGER NOT NULL DEFAULT 0,
    first_seen_session INTEGER,
    state_notes        TEXT    NOT NULL DEFAULT '',
    updated_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(campaign_name, name)
);

-- Entity state: Factions
CREATE TABLE IF NOT EXISTS factions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    standing      INTEGER NOT NULL DEFAULT 0,
    notes         TEXT    NOT NULL DEFAULT '',
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(campaign_name, name)
);

-- Character roster
CREATE TABLE IF NOT EXISTS player_characters (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name  TEXT    NOT NULL,
    player_name    TEXT    NOT NULL DEFAULT '',
    character_name TEXT    NOT NULL,
    class          TEXT    NOT NULL DEFAULT '',
    level          INTEGER NOT NULL DEFAULT 1,
    backstory_notes TEXT   NOT NULL DEFAULT '',
    active         INTEGER NOT NULL DEFAULT 1,
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(campaign_name, character_name)
);

CREATE TABLE IF NOT EXISTS pc_inventory (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    pc_id            INTEGER NOT NULL REFERENCES player_characters(id) ON DELETE CASCADE,
    item_name        TEXT    NOT NULL,
    description      TEXT    NOT NULL DEFAULT '',
    acquired_session INTEGER,
    notable          INTEGER NOT NULL DEFAULT 1
);

-- Narrative threads
CREATE TABLE IF NOT EXISTS threads (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name      TEXT    NOT NULL,
    title              TEXT    NOT NULL,
    type               TEXT    NOT NULL DEFAULT 'quest',
    status             TEXT    NOT NULL DEFAULT 'active',
    description        TEXT    NOT NULL DEFAULT '',
    introduced_session INTEGER,
    resolved_session   INTEGER,
    updated_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS thread_sessions (
    thread_id  INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    PRIMARY KEY (thread_id, session_id)
);
"""


def init_db(db_path: str) -> None:
    """Create the database and all tables if they do not already exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = _connect(db_path)
    try:
        conn.executescript(_DDL)
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        if row is None:
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (_SCHEMA_VERSION,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Sessions & debrief
# ---------------------------------------------------------------------------

def create_session(
    db_path: str,
    campaign_name: str,
    session_number: int,
    session_date: date | None = None,
) -> int:
    """Insert a new session row and return its id."""
    date_str = session_date.isoformat() if session_date else None
    with _cursor(db_path) as cur:
        cur.execute(
            "INSERT INTO sessions (campaign_name, session_number, session_date) VALUES (?, ?, ?)",
            (campaign_name, session_number, date_str),
        )
        return cur.lastrowid  # type: ignore[return-value]


def save_debrief_answers(
    db_path: str,
    session_id: int,
    answers: dict[str, str],
) -> None:
    """Upsert debrief answers for a session."""
    with _cursor(db_path) as cur:
        for key, text in answers.items():
            cur.execute(
                """INSERT INTO debrief_answers (session_id, question_key, answer_text)
                   VALUES (?, ?, ?)
                   ON CONFLICT DO NOTHING""",
                (session_id, key, text),
            )


def get_recent_sessions(db_path: str, campaign_name: str, n: int = 3) -> list[sqlite3.Row]:
    """Return the n most recent sessions for a campaign, newest first."""
    conn = _connect(db_path)
    try:
        return conn.execute(
            """SELECT s.*, GROUP_CONCAT(da.question_key || '::' || da.answer_text, '|||') AS answers
               FROM sessions s
               LEFT JOIN debrief_answers da ON da.session_id = s.id
               WHERE s.campaign_name = ?
               GROUP BY s.id
               ORDER BY s.session_number DESC
               LIMIT ?""",
            (campaign_name, n),
        ).fetchall()
    finally:
        conn.close()


def save_recap(db_path: str, session_id: int, recap_text: str) -> int:
    """Save a generated recap and return its id."""
    with _cursor(db_path) as cur:
        cur.execute(
            "INSERT INTO recaps (session_id, recap_text) VALUES (?, ?)",
            (session_id, recap_text),
        )
        return cur.lastrowid  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Entity state: NPCs
# ---------------------------------------------------------------------------

def upsert_npc(db_path: str, campaign_name: str, name: str, **fields: object) -> None:
    allowed = {"role", "disposition", "last_seen_session", "notes"}
    data = {k: v for k, v in fields.items() if k in allowed}
    data["updated_at"] = datetime.utcnow().isoformat()
    with _cursor(db_path) as cur:
        cur.execute(
            """INSERT INTO npcs (campaign_name, name, role, disposition, last_seen_session, notes, updated_at)
               VALUES (:campaign, :name, :role, :disposition, :last_seen, :notes, :updated_at)
               ON CONFLICT(campaign_name, name) DO UPDATE SET
                 role              = COALESCE(:role, role),
                 disposition       = COALESCE(:disposition, disposition),
                 last_seen_session = COALESCE(:last_seen, last_seen_session),
                 notes             = COALESCE(:notes, notes),
                 updated_at        = :updated_at""",
            {
                "campaign": campaign_name,
                "name": name,
                "role": data.get("role"),
                "disposition": data.get("disposition"),
                "last_seen": data.get("last_seen_session"),
                "notes": data.get("notes"),
                "updated_at": data["updated_at"],
            },
        )


def get_npcs(db_path: str, campaign_name: str, disposition: str | None = None) -> list[sqlite3.Row]:
    conn = _connect(db_path)
    try:
        if disposition:
            return conn.execute(
                "SELECT * FROM npcs WHERE campaign_name = ? AND disposition = ? ORDER BY name",
                (campaign_name, disposition),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM npcs WHERE campaign_name = ? ORDER BY name",
            (campaign_name,),
        ).fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Entity state: Locations
# ---------------------------------------------------------------------------

def upsert_location(db_path: str, campaign_name: str, name: str, **fields: object) -> None:
    allowed = {"visited", "first_seen_session", "state_notes"}
    data = {k: v for k, v in fields.items() if k in allowed}
    data["updated_at"] = datetime.utcnow().isoformat()
    with _cursor(db_path) as cur:
        cur.execute(
            """INSERT INTO locations (campaign_name, name, visited, first_seen_session, state_notes, updated_at)
               VALUES (:campaign, :name, :visited, :first_seen, :state_notes, :updated_at)
               ON CONFLICT(campaign_name, name) DO UPDATE SET
                 visited           = COALESCE(:visited, visited),
                 first_seen_session= COALESCE(:first_seen, first_seen_session),
                 state_notes       = COALESCE(:state_notes, state_notes),
                 updated_at        = :updated_at""",
            {
                "campaign": campaign_name,
                "name": name,
                "visited": int(data.get("visited", 0)),  # type: ignore[arg-type]
                "first_seen": data.get("first_seen_session"),
                "state_notes": data.get("state_notes"),
                "updated_at": data["updated_at"],
            },
        )


def get_visited_locations(db_path: str, campaign_name: str) -> list[sqlite3.Row]:
    conn = _connect(db_path)
    try:
        return conn.execute(
            "SELECT * FROM locations WHERE campaign_name = ? AND visited = 1 ORDER BY name",
            (campaign_name,),
        ).fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Entity state: Factions
# ---------------------------------------------------------------------------

def upsert_faction(db_path: str, campaign_name: str, name: str, **fields: object) -> None:
    allowed = {"standing", "notes"}
    data = {k: v for k, v in fields.items() if k in allowed}
    data["updated_at"] = datetime.utcnow().isoformat()
    with _cursor(db_path) as cur:
        cur.execute(
            """INSERT INTO factions (campaign_name, name, standing, notes, updated_at)
               VALUES (:campaign, :name, :standing, :notes, :updated_at)
               ON CONFLICT(campaign_name, name) DO UPDATE SET
                 standing   = COALESCE(:standing, standing),
                 notes      = COALESCE(:notes, notes),
                 updated_at = :updated_at""",
            {
                "campaign": campaign_name,
                "name": name,
                "standing": data.get("standing"),
                "notes": data.get("notes"),
                "updated_at": data["updated_at"],
            },
        )


def get_factions(db_path: str, campaign_name: str) -> list[sqlite3.Row]:
    conn = _connect(db_path)
    try:
        return conn.execute(
            "SELECT * FROM factions WHERE campaign_name = ? ORDER BY name",
            (campaign_name,),
        ).fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Character roster
# ---------------------------------------------------------------------------

def upsert_pc(db_path: str, campaign_name: str, character_name: str, **fields: object) -> None:
    allowed = {"player_name", "class", "level", "backstory_notes", "active"}
    data = {k: v for k, v in fields.items() if k in allowed}
    data["updated_at"] = datetime.utcnow().isoformat()
    with _cursor(db_path) as cur:
        cur.execute(
            """INSERT INTO player_characters
                 (campaign_name, character_name, player_name, class, level, backstory_notes, active, updated_at)
               VALUES (:campaign, :char, :player, :class, :level, :backstory, :active, :updated_at)
               ON CONFLICT(campaign_name, character_name) DO UPDATE SET
                 player_name     = COALESCE(:player, player_name),
                 class           = COALESCE(:class, class),
                 level           = COALESCE(:level, level),
                 backstory_notes = COALESCE(:backstory, backstory_notes),
                 active          = COALESCE(:active, active),
                 updated_at      = :updated_at""",
            {
                "campaign": campaign_name,
                "char": character_name,
                "player": data.get("player_name"),
                "class": data.get("class"),
                "level": data.get("level"),
                "backstory": data.get("backstory_notes"),
                "active": int(data.get("active", 1)),  # type: ignore[arg-type]
                "updated_at": data["updated_at"],
            },
        )


def get_active_pcs(db_path: str, campaign_name: str) -> list[sqlite3.Row]:
    conn = _connect(db_path)
    try:
        return conn.execute(
            "SELECT * FROM player_characters WHERE campaign_name = ? AND active = 1 ORDER BY character_name",
            (campaign_name,),
        ).fetchall()
    finally:
        conn.close()


def add_notable_item(
    db_path: str,
    pc_id: int,
    item_name: str,
    description: str = "",
    session_id: int | None = None,
) -> None:
    with _cursor(db_path) as cur:
        cur.execute(
            "INSERT INTO pc_inventory (pc_id, item_name, description, acquired_session, notable) VALUES (?, ?, ?, ?, 1)",
            (pc_id, item_name, description, session_id),
        )


# ---------------------------------------------------------------------------
# Narrative threads
# ---------------------------------------------------------------------------

def create_thread(
    db_path: str,
    campaign_name: str,
    title: str,
    type: str,
    description: str,
    session_id: int | None = None,
) -> int:
    with _cursor(db_path) as cur:
        cur.execute(
            """INSERT INTO threads (campaign_name, title, type, description, introduced_session)
               VALUES (?, ?, ?, ?, ?)""",
            (campaign_name, title, type, description, session_id),
        )
        thread_id: int = cur.lastrowid  # type: ignore[assignment]
        if session_id is not None:
            cur.execute(
                "INSERT OR IGNORE INTO thread_sessions (thread_id, session_id) VALUES (?, ?)",
                (thread_id, session_id),
            )
        return thread_id


def resolve_thread(db_path: str, thread_id: int, session_id: int | None = None) -> None:
    with _cursor(db_path) as cur:
        cur.execute(
            "UPDATE threads SET status = 'resolved', resolved_session = ?, updated_at = datetime('now') WHERE id = ?",
            (session_id, thread_id),
        )


def get_active_threads(db_path: str, campaign_name: str) -> list[sqlite3.Row]:
    conn = _connect(db_path)
    try:
        return conn.execute(
            "SELECT * FROM threads WHERE campaign_name = ? AND status = 'active' ORDER BY introduced_session, id",
            (campaign_name,),
        ).fetchall()
    finally:
        conn.close()


def get_threads_for_session(db_path: str, session_id: int) -> list[sqlite3.Row]:
    conn = _connect(db_path)
    try:
        return conn.execute(
            """SELECT t.* FROM threads t
               JOIN thread_sessions ts ON ts.thread_id = t.id
               WHERE ts.session_id = ?
               ORDER BY t.title""",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Campaign state snapshot (for sidebar / recent-progress display)
# ---------------------------------------------------------------------------

def get_campaign_state(db_path: str, campaign_name: str) -> dict:
    """Return a snapshot of the current campaign state.

    Gathers:
    - The most recent session number, date, and its debrief answers
    - Active (unresolved) plot threads
    - Active player characters
    - Counts of tracked NPCs and visited locations

    Returns an empty dict if no sessions have been recorded yet.
    """
    conn = _connect(db_path)
    try:
        # ── Last session ──────────────────────────────────────────────────
        row = conn.execute(
            """SELECT s.id, s.session_number, s.session_date
               FROM sessions s
               WHERE s.campaign_name = ?
               ORDER BY s.session_number DESC
               LIMIT 1""",
            (campaign_name,),
        ).fetchone()

        if row is None:
            return {}

        session_id = row["id"]
        state: dict = {
            "session_number": row["session_number"],
            "session_date": row["session_date"],
        }

        # ── Debrief answers for that session ─────────────────────────────
        answer_rows = conn.execute(
            "SELECT question_key, answer_text FROM debrief_answers WHERE session_id = ?",
            (session_id,),
        ).fetchall()
        state["debrief"] = {r["question_key"]: r["answer_text"] for r in answer_rows}

        # ── Active threads ────────────────────────────────────────────────
        thread_rows = conn.execute(
            """SELECT title, description FROM threads
               WHERE campaign_name = ? AND resolved = 0
               ORDER BY title""",
            (campaign_name,),
        ).fetchall()
        state["active_threads"] = [
            {"title": r["title"], "description": r["description"]}
            for r in thread_rows
        ]

        # ── Active player characters ──────────────────────────────────────
        pc_rows = conn.execute(
            """SELECT name, class_level, player FROM player_characters
               WHERE campaign_name = ? AND active = 1
               ORDER BY name""",
            (campaign_name,),
        ).fetchall()
        state["player_characters"] = [
            {"name": r["name"], "class_level": r["class_level"], "player": r["player"]}
            for r in pc_rows
        ]

        # ── Counts ────────────────────────────────────────────────────────
        state["npc_count"] = conn.execute(
            "SELECT COUNT(*) FROM npcs WHERE campaign_name = ?", (campaign_name,)
        ).fetchone()[0]

        state["location_count"] = conn.execute(
            "SELECT COUNT(*) FROM locations WHERE campaign_name = ?", (campaign_name,)
        ).fetchone()[0]

        return state
    finally:
        conn.close()

