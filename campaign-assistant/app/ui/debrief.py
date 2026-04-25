from __future__ import annotations

"""Post-session debrief tab."""

from datetime import date

import streamlit as st

from ..session.database import (
    create_session,
    save_debrief_answers,
    get_recent_sessions,
)
from ..session.questions import load_questions


def render(settings, campaign_name: str) -> None:
    st.header("Post-Session Debrief")
    st.caption("Record what happened this session. Answers are saved to the database for future recaps.")

    questions = load_questions()  # uses DEFAULT_QUESTIONS; campaigns can add questions.json later

    # Auto-detect next session number
    recent = get_recent_sessions(settings.database_path, campaign_name, n=1)
    next_number = (recent[0]["session_number"] + 1) if recent else 1

    col1, col2 = st.columns([1, 2])
    with col1:
        session_number = st.number_input("Session number", min_value=1, value=next_number, step=1)
    with col2:
        session_date = st.date_input("Session date", value=date.today())

    st.divider()

    answers: dict[str, str] = {}
    for q in questions:
        answers[q.key] = st.text_area(q.text, key=f"debrief_{q.key}", height=100)

    st.divider()
    if st.button("Save Debrief", type="primary"):
        filled = {k: v for k, v in answers.items() if v.strip()}
        if not filled:
            st.warning("Please answer at least one question before saving.")
        else:
            session_id = create_session(
                settings.database_path,
                campaign_name,
                int(session_number),
                session_date,
            )
            save_debrief_answers(settings.database_path, session_id, filled)
            st.success(f"Session {session_number} saved. {len(filled)} answer(s) recorded.")

            with st.expander("Review saved answers"):
                for q in questions:
                    if q.key in filled:
                        st.markdown(f"**{q.text}**")
                        st.write(filled[q.key])
