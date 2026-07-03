"""Anthropic (Claude) LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the anthropic package installed.
"""
from __future__ import annotations

from .base import BaseLLMClient, LLMError


class AnthropicClient(BaseLLMClient):
    """Stub for the Anthropic Claude client — implemented in Phase 2."""

    #: Supported models (populated in Phase 2 when the real client is built).
    SUPPORTED_MODELS = [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-3-5",
    ]

    def __init__(self, api_key: str = "", model: str = "claude-sonnet-4-5", **kwargs: object) -> None:
        self.api_key = api_key
        self.model = model

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "Anthropic (Claude) is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )

    def list_models(self) -> list[str]:
        return list(self.SUPPORTED_MODELS)
