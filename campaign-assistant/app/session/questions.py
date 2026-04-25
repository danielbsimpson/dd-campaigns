from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Question:
    key: str
    text: str


# Standard post-session debrief questions.
DEFAULT_QUESTIONS: list[Question] = [
    Question(
        key="summary",
        text="Give a brief summary of what happened this session.",
    ),
    Question(
        key="npcs",
        text="Which NPCs did the party interact with meaningfully? What was the nature of those interactions?",
    ),
    Question(
        key="locations",
        text="Which locations were visited or had their situation change during this session?",
    ),
    Question(
        key="threads_advanced",
        text="Which active quests or plot threads advanced, and how?",
    ),
    Question(
        key="threads_resolved",
        text="Were any quests or plot threads resolved or abandoned? If so, which ones and how?",
    ),
    Question(
        key="threads_new",
        text="Did this session introduce any new quests, mysteries, or plot hooks?",
    ),
    Question(
        key="player_decisions",
        text="What key player decisions or consequences should be remembered going forward?",
    ),
    Question(
        key="items",
        text="Did the party acquire or lose any notable items (quest items, unique magic, character-defining gear)?",
    ),
    Question(
        key="dm_notes",
        text="Any DM prep notes or reminders for next session?",
    ),
]


def load_questions(campaign_folder: str | None = None) -> list[Question]:
    """Return the debrief question list.

    If a ``questions.json`` file exists in ``campaign_folder``, it is merged
    with (or replaces) the defaults depending on its ``mode`` field:

    - ``"override"``: replaces the default list entirely.
    - ``"extend"`` (default): appends extra questions after the defaults.

    ``questions.json`` format::

        {
            "mode": "extend",
            "questions": [
                {"key": "custom_key", "text": "Your custom question?"}
            ]
        }
    """
    if not campaign_folder:
        return list(DEFAULT_QUESTIONS)

    override_path = Path(campaign_folder) / "questions.json"
    if not override_path.exists():
        return list(DEFAULT_QUESTIONS)

    try:
        data = json.loads(override_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return list(DEFAULT_QUESTIONS)

    custom = [Question(key=q["key"], text=q["text"]) for q in data.get("questions", [])]
    mode = data.get("mode", "extend")

    if mode == "override":
        return custom
    return list(DEFAULT_QUESTIONS) + custom
