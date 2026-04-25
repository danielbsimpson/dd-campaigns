from __future__ import annotations

"""Campaign Assistant — Streamlit entry point.

Run with:
    streamlit run app/main.py
"""

import json
import sys
from pathlib import Path

# Allow `streamlit run app/main.py` (script mode) to find the package.
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from app.config import load_settings
from app.campaign.loader import load_campaign, list_campaigns
from app.session.database import init_db, get_campaign_state
from app.ui import query as query_ui
from app.ui import debrief as debrief_ui
from app.ui import recap as recap_ui
from app.ui import settings as settings_ui
from app.ui import world as world_ui

st.set_page_config(
    page_title="Campaign Assistant",
    page_icon="🎲",
    layout="wide",
)

# ------------------------------------------------------------------
# Load settings (config.py + optional settings.json overrides)
# ------------------------------------------------------------------
_SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"


def _merge_settings_json(base_settings):
    """Apply any values saved via the Settings UI over the env-derived base."""
    if not _SETTINGS_FILE.exists():
        return base_settings
    try:
        overrides = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return base_settings
    # Patch the settings object with saved values
    for key, value in overrides.items():
        if hasattr(base_settings, key):
            object.__setattr__(base_settings, key, value)
    return base_settings


try:
    settings = load_settings()
    settings = _merge_settings_json(settings)
    config_error: str | None = None
except SystemExit as exc:
    settings = None
    config_error = str(exc)

# ------------------------------------------------------------------
# Init DB (safe to call on every startup — only creates if missing)
# ------------------------------------------------------------------
if settings:
    init_db(settings.database_path)

# ------------------------------------------------------------------
# Campaign list (cached per root path)
# ------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _list_campaigns_cached(root: str) -> list[dict]:
    return list_campaigns(root)


@st.cache_data(show_spinner="Loading campaign files…")
def _load_campaign_cached(folder: str) -> dict[str, str]:
    try:
        return load_campaign(folder)
    except Exception:
        return {}


# ------------------------------------------------------------------
# Resolve active campaign from session_state or settings default
# ------------------------------------------------------------------
available_campaigns: list[dict] = []
active_campaign_folder: str = ""
active_campaign_name: str = ""
campaign_files: dict[str, str] = {}

if settings:
    available_campaigns = _list_campaigns_cached(settings.campaigns_root)
    campaign_names = [c["name"] for c in available_campaigns]

    # Determine the default selection: last saved setting or first available
    default_folder = settings.campaign_folder
    default_name = (
        Path(default_folder).name if default_folder else
        (campaign_names[0] if campaign_names else "")
    )
    if "active_campaign_name" not in st.session_state:
        st.session_state.active_campaign_name = default_name

    active_campaign_name = st.session_state.active_campaign_name
    active_campaign_folder = next(
        (c["path"] for c in available_campaigns if c["name"] == active_campaign_name),
        default_folder,
    )
    if active_campaign_folder:
        campaign_files = _load_campaign_cached(active_campaign_folder)

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.title("🎲 Campaign Assistant")

    if settings and available_campaigns:
        campaign_names = [c["name"] for c in available_campaigns]
        current_idx = campaign_names.index(active_campaign_name) if active_campaign_name in campaign_names else 0

        selected = st.selectbox(
            "Campaign",
            campaign_names,
            index=current_idx,
            key="_sidebar_campaign_select",
        )
        if selected != st.session_state.active_campaign_name:
            st.session_state.active_campaign_name = selected
            # Clear any cached per-campaign state
            st.session_state.pop("query_history", None)
            st.rerun()

        # ── LLM info ─────────────────────────────────────────────────
        st.divider()
        provider_label = settings.llm_provider.capitalize()
        model = getattr(settings, f"{settings.llm_provider}_model", "")
        st.caption(f"**Provider:** {provider_label}  \n**Model:** {model}")

        # ── Recent campaign state card ────────────────────────────────
        st.divider()
        state = get_campaign_state(settings.database_path, active_campaign_name)
        if state:
            st.markdown("**Last Session**")
            date_str = f" — {state['session_date']}" if state.get("session_date") else ""
            st.caption(f"Session {state['session_number']}{date_str}")

            debrief = state.get("debrief", {})
            if debrief.get("summary"):
                with st.expander("Session summary", expanded=False):
                    st.write(debrief["summary"])
            if debrief.get("player_decisions"):
                with st.expander("Key decisions", expanded=False):
                    st.write(debrief["player_decisions"])

            threads = state.get("active_threads", [])
            if threads:
                with st.expander(f"Active threads ({len(threads)})", expanded=False):
                    for t in threads:
                        st.markdown(f"• **{t['title']}**")
                        if t.get("description"):
                            st.caption(t["description"])

            pcs = state.get("player_characters", [])
            if pcs:
                with st.expander(f"Party ({len(pcs)})", expanded=False):
                    for pc in pcs:
                        label = pc["name"]
                        if pc.get("class_level"):
                            label += f" — {pc['class_level']}"
                        if pc.get("player"):
                            label += f" ({pc['player']})"
                        st.caption(label)

            counts = []
            if state.get("npc_count"):
                counts.append(f"{state['npc_count']} NPCs")
            if state.get("location_count"):
                counts.append(f"{state['location_count']} locations")
            if counts:
                st.caption("Tracked: " + " · ".join(counts))
        else:
            st.caption("No sessions recorded yet.")

    elif settings and not available_campaigns:
        st.warning("No campaigns found in the configured campaigns root.")
    else:
        st.error("Configuration error — see the Settings tab.")

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab_query, tab_debrief, tab_recap, tab_world, tab_settings = st.tabs(
    ["Query", "Debrief", "Recap", "World State", "Settings"]
)

if config_error:
    for tab in (tab_query, tab_debrief, tab_recap, tab_world):
        with tab:
            st.error(f"Cannot start: {config_error}")
            st.info("Fix the configuration in the Settings tab or your `.env` file, then refresh.")

with tab_settings:
    if settings:
        settings_ui.render(settings)
    else:
        from app.config import Settings as _Settings  # noqa: F401
        _fallback = _Settings.model_construct(
            llm_provider="ollama",
            ollama_base_url="http://localhost:11434",
            ollama_model="llama3.1:8b",
            lmstudio_base_url="http://localhost:1234",
            lmstudio_model="",
            campaigns_root="",
            campaign_folder="",
            database_path="./sessions.db",
        )
        settings_ui.render(_fallback)

if settings and not config_error and active_campaign_folder:
    with tab_query:
        query_ui.render(settings, campaign_files, active_campaign_name)

    with tab_debrief:
        debrief_ui.render(settings, active_campaign_name)

    with tab_recap:
        recap_ui.render(settings, campaign_files, active_campaign_name)

    with tab_world:
        world_ui.render(settings, active_campaign_name)
elif settings and not config_error and not active_campaign_folder:
    for tab in (tab_query, tab_debrief, tab_recap, tab_world):
        with tab:
            st.info("Select a campaign from the sidebar to get started.")
