from __future__ import annotations

"""World state browser tab — NPCs, Locations, Threads."""

import streamlit as st

from ..session.database import (
    get_npcs,
    get_active_threads,
    get_factions,
    get_visited_locations,
    upsert_npc,
    upsert_location,
    create_thread,
    resolve_thread,
)


def render(settings, campaign_name: str) -> None:
    db = settings.database_path

    st.header("World State")
    npc_tab, location_tab, thread_tab = st.tabs(["NPCs", "Locations", "Threads"])

    with npc_tab:
        _npc_panel(db, campaign_name)

    with location_tab:
        _location_panel(db, campaign_name)

    with thread_tab:
        _thread_panel(db, campaign_name)


def _npc_panel(db: str, campaign_name: str) -> None:
    st.subheader("NPCs")

    dispositions = ["", "friendly", "neutral", "hostile", "unknown", "dead"]
    filter_disp = st.selectbox("Filter by disposition", dispositions, index=0)
    npcs = get_npcs(db, campaign_name, disposition=filter_disp if filter_disp else None)

    if not npcs:
        st.info("No NPCs recorded yet. Add one below.")
    else:
        for npc in npcs:
            with st.expander(f"{npc['name']} — {npc['disposition']}"):
                new_disp = st.selectbox(
                    "Disposition",
                    ["friendly", "neutral", "hostile", "unknown", "dead"],
                    index=["friendly", "neutral", "hostile", "unknown", "dead"].index(npc["disposition"])
                    if npc["disposition"] in ["friendly", "neutral", "hostile", "unknown", "dead"] else 3,
                    key=f"disp_{npc['id']}",
                )
                new_notes = st.text_area("Notes", value=npc["notes"], key=f"notes_{npc['id']}")
                if st.button("Save", key=f"save_npc_{npc['id']}"):
                    upsert_npc(db, campaign_name, npc["name"], disposition=new_disp, notes=new_notes)
                    st.success("Saved.")
                    st.rerun()

    st.divider()
    with st.expander("Add NPC"):
        name = st.text_input("Name", key="new_npc_name")
        role = st.text_input("Role", key="new_npc_role")
        disp = st.selectbox("Disposition", ["unknown", "friendly", "neutral", "hostile"], key="new_npc_disp")
        if st.button("Add NPC") and name.strip():
            upsert_npc(db, campaign_name, name.strip(), role=role, disposition=disp)
            st.success(f"{name} added.")
            st.rerun()


def _location_panel(db: str, campaign_name: str) -> None:
    st.subheader("Locations")

    locations = get_visited_locations(db, campaign_name)

    if not locations:
        st.info("No visited locations recorded yet.")
    else:
        for loc in locations:
            with st.expander(loc["name"]):
                new_notes = st.text_area("State notes", value=loc["state_notes"], key=f"loc_notes_{loc['id']}")
                if st.button("Save", key=f"save_loc_{loc['id']}"):
                    upsert_location(db, campaign_name, loc["name"], state_notes=new_notes)
                    st.success("Saved.")
                    st.rerun()

    st.divider()
    with st.expander("Add Location"):
        name = st.text_input("Location name", key="new_loc_name")
        visited = st.checkbox("Mark as visited", value=True, key="new_loc_visited")
        notes = st.text_area("State notes", key="new_loc_notes")
        if st.button("Add Location") and name.strip():
            upsert_location(db, campaign_name, name.strip(), visited=visited, state_notes=notes)
            st.success(f"{name} added.")
            st.rerun()


def _thread_panel(db: str, campaign_name: str) -> None:
    st.subheader("Narrative Threads")

    threads = get_active_threads(db, campaign_name)

    if not threads:
        st.info("No active threads. Add one below.")
    else:
        for thread in threads:
            with st.expander(f"[{thread['type'].upper()}] {thread['title']}"):
                st.write(thread["description"])
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"Introduced: session {thread['introduced_session'] or '?'}")
                with col2:
                    if st.button("Resolve", key=f"resolve_{thread['id']}"):
                        resolve_thread(db, thread["id"])
                        st.success("Thread resolved.")
                        st.rerun()

    st.divider()
    with st.expander("Add Thread"):
        title = st.text_input("Title", key="new_thread_title")
        ttype = st.selectbox("Type", ["quest", "mystery", "foreshadowing", "consequence"], key="new_thread_type")
        desc = st.text_area("Description", key="new_thread_desc")
        if st.button("Add Thread") and title.strip():
            create_thread(db, campaign_name, title.strip(), ttype, desc)
            st.success(f"Thread '{title}' added.")
            st.rerun()
