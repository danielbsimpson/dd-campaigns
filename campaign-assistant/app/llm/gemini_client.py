"""Google Gemini LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the google-generativeai package installed.
"""
from __future__ import annotations

from .base import BaseLLMClient, LLMError


class GeminiClient(BaseLLMClient):
    """Stub for the Google Gemini client — implemented in Phase 2."""

    #: Supported models (populated in Phase 2 when the real client is built).
    SUPPORTED_MODELS = [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    def __init__(self, api_key: str = "", model: str = "gemini-2.0-flash", **kwargs: object) -> None:
        self.api_key = api_key
        self.model = model

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "Google Gemini is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )

    def list_models(self) -> list[str]:
        return list(self.SUPPORTED_MODELS)
