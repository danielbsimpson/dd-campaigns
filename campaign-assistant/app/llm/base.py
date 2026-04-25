from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class BaseLLMClient(ABC):
    """Common interface for all LLM backends."""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Send a prompt and return the model's text response.

        Args:
            system: The system prompt (instructions / context).
            user:   The user message (the DM's question or request).

        Returns:
            The model's response as a plain string.

        Raises:
            LLMError: On any provider-level error (connection, auth, rate limit).
        """

    def list_models(self) -> list[str]:
        """Return available model names for this backend.

        Override in clients that can query their server for a model list.
        Returns an empty list by default (used for cloud stubs).
        """
        return []

    def detect_gpu(self) -> bool | None:
        """Return True if the backend is confirmed to be using a GPU.

        Returns None if the backend cannot determine this (e.g. cloud providers).
        Override in local clients that expose hardware info.
        """
        return None


class LLMError(Exception):
    """Raised when an LLM backend returns an error the UI should surface."""


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

@dataclass
class ProviderInfo:
    client_class: type[BaseLLMClient]
    # Fields required from config/settings to construct the client.
    required_fields: list[str] = field(default_factory=list)
    # Optional fields with their default values.
    optional_fields: dict[str, Any] = field(default_factory=dict)
    is_local: bool = True


# Registry maps provider key -> ProviderInfo.
# Phase 1: local providers only. Phase 2 will add cloud entries.
PROVIDER_REGISTRY: dict[str, ProviderInfo] = {}


def register_provider(key: str, info: ProviderInfo) -> None:
    PROVIDER_REGISTRY[key] = info


def get_llm_client(provider: str, config: dict[str, Any]) -> BaseLLMClient:
    """Construct and return the appropriate LLM client.

    Args:
        provider: Provider key, e.g. ``"ollama"`` or ``"lmstudio"``.
        config:   Dict of config values (e.g. from Settings or the settings UI).

    Raises:
        LLMError: If the provider is unknown or required config fields are missing.
    """
    info = PROVIDER_REGISTRY.get(provider)
    if info is None:
        known = ", ".join(PROVIDER_REGISTRY) or "none registered"
        raise LLMError(
            f"Unknown provider '{provider}'. Known providers: {known}."
        )

    missing = [f for f in info.required_fields if not config.get(f)]
    if missing:
        raise LLMError(
            f"Provider '{provider}' is missing required config fields: "
            + ", ".join(missing)
        )

    kwargs = {**info.optional_fields, **{k: config[k] for k in config if k in info.required_fields + list(info.optional_fields)}}
    return info.client_class(**kwargs)
