"""Mistral AI LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the mistralai package installed.
"""
from __future__ import annotations

from .base import BaseLLMClient, LLMError


class MistralClient(BaseLLMClient):
    """Stub for the Mistral AI client — implemented in Phase 2."""

    #: Supported models (populated in Phase 2 when the real client is built).
    SUPPORTED_MODELS = [
        "mistral-large-latest",
        "mistral-small-latest",
        "open-mixtral-8x7b",
    ]

    def __init__(self, api_key: str = "", model: str = "mistral-large-latest", **kwargs: object) -> None:
        self.api_key = api_key
        self.model = model

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "Mistral AI is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )

    def list_models(self) -> list[str]:
        return list(self.SUPPORTED_MODELS)
