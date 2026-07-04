"""OpenAI LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the openai package installed.
"""
from __future__ import annotations

from .base import CloudStubClient


class OpenAIClient(CloudStubClient):
    """Stub for the OpenAI GPT client — implemented in Phase 2."""

    PROVIDER_LABEL = "OpenAI"
    DEFAULT_MODEL = "gpt-4o"
    SUPPORTED_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
    ]
