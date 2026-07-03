"""Groq LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the groq package installed.
"""
from __future__ import annotations

from .base import BaseLLMClient, LLMError


class GroqClient(BaseLLMClient):
    """Stub for the Groq client — implemented in Phase 2."""

    #: Supported models (populated in Phase 2 when the real client is built).
    SUPPORTED_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ]

    def __init__(self, api_key: str = "", model: str = "llama-3.3-70b-versatile", **kwargs: object) -> None:
        self.api_key = api_key
        self.model = model

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "Groq is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )

    def list_models(self) -> list[str]:
        return list(self.SUPPORTED_MODELS)
