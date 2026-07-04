"""Anthropic (Claude) LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the anthropic package installed.
"""
from __future__ import annotations

from .base import CloudStubClient


class AnthropicClient(CloudStubClient):
    """Stub for the Anthropic Claude client — implemented in Phase 2."""

    PROVIDER_LABEL = "Anthropic (Claude)"
    DEFAULT_MODEL = "claude-sonnet-4-5"
    SUPPORTED_MODELS = [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-3-5",
    ]
