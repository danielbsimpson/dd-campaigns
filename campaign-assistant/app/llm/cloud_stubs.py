"""Cloud provider stubs — Phase 2.

These classes satisfy the registry type contract so the provider registry
can be fully populated at import time. The complete() method on each raises
NotImplementedError until Phase 2 implements the real client.
"""
from __future__ import annotations

from .base import BaseLLMClient, LLMError


class AnthropicClient(BaseLLMClient):
    def __init__(self, **kwargs: object) -> None:
        pass

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "Anthropic (Claude) is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )


class OpenAIClient(BaseLLMClient):
    def __init__(self, **kwargs: object) -> None:
        pass

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "OpenAI is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )


class GeminiClient(BaseLLMClient):
    def __init__(self, **kwargs: object) -> None:
        pass

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "Google Gemini is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )


class GroqClient(BaseLLMClient):
    def __init__(self, **kwargs: object) -> None:
        pass

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "Groq is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )


class MistralClient(BaseLLMClient):
    def __init__(self, **kwargs: object) -> None:
        pass

    def complete(self, system: str, user: str) -> str:
        raise LLMError(
            "Mistral AI is not yet configured. "
            "Cloud providers are enabled in Phase 2."
        )
