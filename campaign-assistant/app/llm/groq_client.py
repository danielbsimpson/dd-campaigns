"""Groq LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the groq package installed.
"""
from __future__ import annotations

from .base import CloudStubClient


class GroqClient(CloudStubClient):
    """Stub for the Groq client — implemented in Phase 2."""

    PROVIDER_LABEL = "Groq"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    SUPPORTED_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ]
