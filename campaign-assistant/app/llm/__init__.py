from .base import BaseLLMClient, LLMError, PROVIDER_REGISTRY, get_llm_client

# Import local clients to trigger their register_provider() calls.
from . import ollama_client, lmstudio_client  # noqa: F401

# Cloud stubs are imported lazily in Phase 2.

__all__ = [
    "BaseLLMClient",
    "LLMError",
    "PROVIDER_REGISTRY",
    "get_llm_client",
]
