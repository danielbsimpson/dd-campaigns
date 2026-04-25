from __future__ import annotations

"""In-session query tab."""

import streamlit as st

from ..llm import get_llm_client, LLMError
from ..session.memory import build_query_context


def _load_prompt_template() -> str:
    from pathlib import Path
    path = Path(__file__).parent.parent.parent / "prompts" / "query.txt"
    return path.read_text(encoding="utf-8")


def render(settings, campaign_files: dict[str, str], campaign_name: str) -> None:
    st.header("In-Session Query")
    st.caption("Ask a question about the campaign. The assistant answers only from campaign content.")

    if "query_history" not in st.session_state:
        st.session_state.query_history = []

    with st.form("query_form", clear_on_submit=True):
        question = st.text_area("Your question", height=80, placeholder="e.g. What is Alcalde Vásquez's motivation?")
        submitted = st.form_submit_button("Ask")

    if submitted and question.strip():
        with st.spinner("Thinking…"):
            try:
                context = build_query_context(
                    db_path=settings.database_path,
                    campaign_name=campaign_name,
                    campaign_files=campaign_files,
                    query_text=question,
                )
                system = _load_prompt_template().replace("{campaign_context}", context)
                client = get_llm_client(
                    settings.llm_provider,
                    {
                        "base_url": getattr(settings, f"{settings.llm_provider}_base_url", ""),
                        "model": getattr(settings, f"{settings.llm_provider}_model", ""),
                    },
                )
                answer = client.complete(system=system, user=question)
                st.session_state.query_history.insert(0, {"q": question, "a": answer})
            except LLMError as exc:
                st.error(str(exc))

    # Display history
    for entry in st.session_state.query_history:
        with st.container(border=True):
            st.markdown(f"**Q:** {entry['q']}")
            st.markdown(entry["a"])
