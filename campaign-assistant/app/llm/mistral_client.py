"""Mistral AI LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the mistralai package installed.
"""
from __future__ import annotations

from .base import CloudStubClient


class MistralClient(CloudStubClient):
    """Stub for the Mistral AI client — implemented in Phase 2."""

    PROVIDER_LABEL = "Mistral AI"
    DEFAULT_MODEL = "mistral-large-latest"
    SUPPORTED_MODELS = [
        "mistral-large-latest",
        "mistral-small-latest",
        "open-mixtral-8x7b",
    ]
