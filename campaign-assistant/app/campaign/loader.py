from __future__ import annotations

import os
from pathlib import Path

# Subfolder names to skip when scanning a campaign folder.
_SKIP_DIRS = {"assets", "maps", "tokens"}

# File names to collect (exact match, case-insensitive).
_NAMED_FILES = {"readme.md", "characters.md", "creatures.md"}


def list_campaigns(campaigns_root: str) -> list[dict[str, str]]:
    """Scan a campaigns root directory and return metadata for each campaign.

    A valid campaign sub-folder must contain at least one ``.md`` or ``.txt``
    file directly at its root level.

    Args:
        campaigns_root: Absolute path to the directory that contains campaign
            sub-folders (e.g. ``/path/to/campaigns``).

    Returns:
        List of dicts with keys ``"name"`` (folder display name) and
        ``"path"`` (absolute path string), sorted alphabetically by name.
    """
    root = Path(campaigns_root)
    if not root.is_dir():
        return []

    campaigns: list[dict[str, str]] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        # Must contain at least one .md or .txt file at root level
        has_content = any(
            f.suffix.lower() in {".md", ".txt"}
            for f in entry.iterdir()
            if f.is_file()
        )
        if has_content:
            campaigns.append({"name": entry.name, "path": str(entry)})

    return campaigns


def load_campaign(campaign_folder: str) -> dict[str, str]:
    """Scan a campaign folder and return its content as a dict.

    Collects:
    - ``README.md``, ``characters.md``, ``creatures.md`` (if present)
    - Any ``.txt`` file at the root level

    Skips ``assets/``, ``maps/``, ``tokens/`` subfolders.

    Args:
        campaign_folder: Absolute path to the campaign root directory.

    Returns:
        Dict mapping filename (lowercase) to file text content.

    Raises:
        FileNotFoundError: If the folder does not exist.
        OSError:           On read errors.
    """
    root = Path(campaign_folder)
    if not root.is_dir():
        raise FileNotFoundError(f"Campaign folder not found: {campaign_folder}")

    content: dict[str, str] = {}

    for entry in root.iterdir():
        if entry.is_dir():
            continue
        name_lower = entry.name.lower()
        if name_lower in _NAMED_FILES or entry.suffix.lower() == ".txt":
            text = entry.read_text(encoding="utf-8", errors="replace")
            content[entry.name] = text

    return content
