from __future__ import annotations

"""Settings tab — Phase 1: local providers only."""

import json
from pathlib import Path

import streamlit as st

from ..llm import get_llm_client, LLMError
from ..llm.ollama_client import OllamaClient
from ..llm.lmstudio_client import LMStudioClient

_SETTINGS_FILE = Path(__file__).parent.parent.parent / "settings.json"


def _load_saved() -> dict:
    if _SETTINGS_FILE.exists():
        try:
            return json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save(data: dict) -> None:
    _SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def render(settings) -> None:
    st.header("Settings")

    saved = _load_saved()

    # ------------------------------------------------------------------
    # LLM provider
    # ------------------------------------------------------------------
    st.subheader("LLM Provider")

    provider_options = ["ollama", "lmstudio"]
    current_provider = saved.get("llm_provider", settings.llm_provider)
    provider = st.radio(
        "Select local provider",
        provider_options,
        index=provider_options.index(current_provider) if current_provider in provider_options else 0,
        horizontal=True,
    )

    if provider == "ollama":
        _ollama_section(saved, settings)
    else:
        _lmstudio_section(saved, settings)

    st.divider()
    st.subheader("Phase 2 — Cloud Providers")
    st.info(
        "Cloud providers (Anthropic, OpenAI, Gemini, Groq, Mistral) will be configurable here in Phase 2. "
        "Get everything working locally first.",
        icon="ℹ️",
    )

    st.divider()
    st.subheader("Campaigns Root")
    st.caption("Path to the directory that contains all your campaign sub-folders.")
    campaigns_root = st.text_input(
        "Campaigns root path",
        value=saved.get("campaigns_root", settings.campaigns_root),
        placeholder="/absolute/path/to/campaigns",
        key="campaigns_root",
    )
    root_valid = Path(campaigns_root).is_dir() if campaigns_root else False
    if campaigns_root:
        if root_valid:
            from app.campaign.loader import list_campaigns
            found = list_campaigns(campaigns_root)
            if found:
                st.success(f"Found {len(found)} campaign(s): {', '.join(c['name'] for c in found)}")
            else:
                st.warning("Folder exists but no campaigns detected inside it.")
        else:
            st.error("Folder not found — check the path.")

    st.divider()
    if st.button("Save Settings", type="primary"):
        new_settings = {
            "llm_provider": provider,
            "campaigns_root": st.session_state.get("campaigns_root", settings.campaigns_root),
        }
        if provider == "ollama":
            new_settings["ollama_base_url"] = st.session_state.get("ollama_base_url", settings.ollama_base_url)
            new_settings["ollama_model"] = st.session_state.get("ollama_model", settings.ollama_model)
        else:
            new_settings["lmstudio_base_url"] = st.session_state.get("lmstudio_base_url", settings.lmstudio_base_url)
            new_settings["lmstudio_model"] = st.session_state.get("lmstudio_model", settings.lmstudio_model)
        _save(new_settings)
        st.rerun()


def _ollama_section(saved: dict, settings) -> None:
    base_url = st.text_input(
        "Ollama base URL",
        value=saved.get("ollama_base_url", settings.ollama_base_url),
        key="ollama_base_url",
    )

    # Fetch available models
    available_models: list[str] = []
    gpu_detected: bool | None = None
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Refresh models"):
            st.session_state["ollama_models_refreshed"] = True

    if base_url:
        client = OllamaClient(base_url=base_url)
        available_models = client.list_models()
        gpu_detected = client.detect_gpu()

    if available_models:
        current_model = saved.get("ollama_model", settings.ollama_model)
        idx = available_models.index(current_model) if current_model in available_models else 0
        with col1:
            st.selectbox("Model", available_models, index=idx, key="ollama_model")
    else:
        with col1:
            st.text_input(
                "Model",
                value=saved.get("ollama_model", settings.ollama_model),
                key="ollama_model",
                help="Could not fetch model list. Is Ollama running?",
            )

    if gpu_detected is True:
        st.success("GPU (CUDA) detected.")
    elif gpu_detected is False:
        st.warning("CPU only — responses will be slower.")

    st.caption(
        "Models that fit on 8 GB VRAM (RTX 4060):  \n"
        "• `llama3.1:8b` (4.9 GB, 128k ctx) — balanced, recommended default  \n"
        "• `qwen2.5:7b` (4.7 GB, 128k ctx) — best for structured output  \n"
        "• `mistral:7b` (4.4 GB, 32k ctx) — fast, reliable  \n"
        "• `gemma3:4b` (3.3 GB, 128k ctx) — crisp, factual  \n"
        "• `phi4-mini` (2.5 GB, 128k ctx) — strong reasoning, small footprint  \n"
        "• `llama3.2:3b` (2.0 GB, 128k ctx) — fastest, minimal VRAM"
    )

    if st.button("Test Connection (Ollama)"):
        _test_connection("ollama", {
            "base_url": st.session_state.get("ollama_base_url", settings.ollama_base_url),
            "model": st.session_state.get("ollama_model", settings.ollama_model),
        })


def _lmstudio_section(saved: dict, settings) -> None:
    base_url = st.text_input(
        "LM Studio base URL",
        value=saved.get("lmstudio_base_url", settings.lmstudio_base_url),
        key="lmstudio_base_url",
    )

    available_models: list[str] = []
    if base_url:
        client = LMStudioClient(base_url=base_url)
        available_models = client.list_models()

    if available_models:
        st.selectbox("Loaded model", available_models, index=0, key="lmstudio_model")
    else:
        st.text_input(
            "Model (auto-detected when server is running)",
            value=saved.get("lmstudio_model", settings.lmstudio_model),
            key="lmstudio_model",
        )

    st.caption("GPU acceleration is automatic via LM Studio's built-in CUDA support.")

    if st.button("Test Connection (LM Studio)"):
        _test_connection("lmstudio", {
            "base_url": st.session_state.get("lmstudio_base_url", settings.lmstudio_base_url),
            "model": st.session_state.get("lmstudio_model", settings.lmstudio_model),
        })


def _test_connection(provider: str, config: dict) -> None:
    with st.spinner("Testing connection…"):
        try:
            client = get_llm_client(provider, config)
            response = client.complete(
                system="You are a helpful assistant. Reply with exactly one word.",
                user="Say 'OK'.",
            )
            st.success(f"Connection successful. Response: {response[:100]}")
        except LLMError as exc:
            st.error(str(exc))
