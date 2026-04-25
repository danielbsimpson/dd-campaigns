from __future__ import annotations

"""Pre-session recap tab."""

import streamlit as st

from ..llm import get_llm_client, LLMError
from ..session.database import get_recent_sessions, save_recap
from ..session.memory import build_recap_context


def _load_prompt_template() -> str:
    from pathlib import Path
    path = Path(__file__).parent.parent.parent / "prompts" / "recap.txt"
    return path.read_text(encoding="utf-8")


def render(settings, campaign_files: dict[str, str], campaign_name: str) -> None:
    st.header("Pre-Session Recap")
    st.caption("Generate a DM briefing based on campaign content and session history.")

    if st.button("Generate Recap", type="primary"):
        with st.spinner("Generating recap…"):
            try:
                context = build_recap_context(
                    db_path=settings.database_path,
                    campaign_name=campaign_name,
                    campaign_files=campaign_files,
                )
                system = _load_prompt_template().replace("{campaign_context}", context)
                client = get_llm_client(
                    settings.llm_provider,
                    {
                        "base_url": getattr(settings, f"{settings.llm_provider}_base_url", ""),
                        "model": getattr(settings, f"{settings.llm_provider}_model", ""),
                    },
                )
                recap_text = client.complete(system=system, user="Generate the pre-session recap briefing.")
                st.session_state["latest_recap"] = recap_text
                st.session_state["latest_recap_saved"] = False
            except LLMError as exc:
                st.error(str(exc))

    if "latest_recap" in st.session_state:
        st.markdown(st.session_state["latest_recap"])
        st.divider()

        recent = get_recent_sessions(settings.database_path, campaign_name, n=1)
        session_id = recent[0]["id"] if recent else None

        if session_id and not st.session_state.get("latest_recap_saved", False):
            if st.button("Save Recap"):
                save_recap(settings.database_path, session_id, st.session_state["latest_recap"])
                st.session_state["latest_recap_saved"] = True
                st.success("Recap saved.")
        elif st.session_state.get("latest_recap_saved"):
            st.info("Recap saved to database.")

    # Previous recaps
    st.divider()
    with st.expander("Previous saved recaps"):
        recent_sessions = get_recent_sessions(settings.database_path, campaign_name, n=5)
        if not recent_sessions:
            st.write("No sessions recorded yet.")
        else:
            for s in recent_sessions:
                st.markdown(f"**Session {s['session_number']}** ({s['session_date'] or 'undated'})")
