"""Shared helpers for the Streamlit UI tabs — prompt loading and client construction."""
from __future__ import annotations

from pathlib import Path

from ..llm import BaseLLMClient, get_llm_client

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
_CONTEXT_PLACEHOLDER = "{campaign_context}"


def render_system_prompt(template_name: str, campaign_context: str) -> str:
    """Load a template from the prompts/ folder and inject the campaign context.

    Args:
        template_name:    File name inside prompts/, e.g. ``"query.txt"``.
        campaign_context: The assembled context block to substitute into the
                          template's ``{campaign_context}`` placeholder.
    """
    template = (_PROMPTS_DIR / template_name).read_text(encoding="utf-8")
    return template.replace(_CONTEXT_PLACEHOLDER, campaign_context)


def client_from_settings(settings) -> BaseLLMClient:
    """Construct the configured LLM client from the app settings object."""
    provider = settings.llm_provider
    return get_llm_client(
        provider,
        {
            "base_url": getattr(settings, f"{provider}_base_url", ""),
            "model": getattr(settings, f"{provider}_model", ""),
        },
    )
