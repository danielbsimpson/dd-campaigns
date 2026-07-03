"""OpenAI LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the openai package installed.
"""
from __future__ import annotations

from .base import BaseLLMClient, LLMError


class OpenAIClient(BaseLLMClient):
    """Stub for the OpenAI GPT client — implemented in Phase 2."""

    #: Supported models (populated in Phase 2 when the real client is built).
    SUPPORTED_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
    ]

    def __init__(self, api_key: str = "", model: str = "gpt-4o", **kwargs: object) -> None:
        self.api_key = api_key
        self.model = model

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "OpenAI is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )

    def list_models(self) -> list[str]:
        return list(self.SUPPORTED_MODELS)
