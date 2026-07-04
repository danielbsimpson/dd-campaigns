"""Google Gemini LLM client — Phase 2 stub.

The complete() method raises LLMError until Phase 2 implements the real client.
Cloud SDK dependencies are NOT imported here so this file is safe to load at
startup without the google-generativeai package installed.
"""
from __future__ import annotations

from .base import CloudStubClient


class GeminiClient(CloudStubClient):
    """Stub for the Google Gemini client — implemented in Phase 2."""

    PROVIDER_LABEL = "Google Gemini"
    DEFAULT_MODEL = "gemini-2.0-flash"
    SUPPORTED_MODELS = [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
