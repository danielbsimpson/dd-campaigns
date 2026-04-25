from __future__ import annotations

import httpx

from .base import BaseLLMClient, LLMError, ProviderInfo, register_provider


class LMStudioClient(BaseLLMClient):
    """LLM client for a locally running LM Studio server (OpenAI-compatible API)."""

    def __init__(
        self,
        base_url: str = "http://localhost:1234",
        model: str = "",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        # LM Studio only loads one model at a time; if model is empty we
        # discover it at call-time from /v1/models.
        self.model = model
        self._timeout = timeout

    # ------------------------------------------------------------------
    # BaseLLMClient interface
    # ------------------------------------------------------------------

    def complete(self, system: str, user: str) -> str:
        model = self.model or self._get_loaded_model()
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            response = httpx.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.ConnectError:
            raise LLMError(
                "Cannot connect to LM Studio. Make sure the local server is running "
                f"at {self.base_url}. Start it from the LM Studio app (Local Server tab)."
            )
        except httpx.TimeoutException:
            raise LLMError(
                f"LM Studio request timed out after {self._timeout}s. "
                "The model may still be loading — try again in a moment."
            )
        except httpx.HTTPStatusError as exc:
            raise LLMError(
                f"LM Studio returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:300]}"
            )

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected LM Studio response format: {data}") from exc

    def list_models(self) -> list[str]:
        """Return model IDs reported by the LM Studio server."""
        try:
            response = httpx.get(
                f"{self.base_url}/v1/models",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return [m["id"] for m in data.get("data", [])]
        except Exception:
            return []

    def detect_gpu(self) -> bool | None:
        """LM Studio always uses GPU (CUDA/Metal) when available — return None
        as we cannot query this directly from the API."""
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_loaded_model(self) -> str:
        """Fetch the first model currently loaded in LM Studio."""
        models = self.list_models()
        if not models:
            raise LLMError(
                "LM Studio is running but no model appears to be loaded. "
                "Load a model from the LM Studio app first."
            )
        return models[0]


# ---------------------------------------------------------------------------
# Register with the provider registry
# ---------------------------------------------------------------------------

register_provider(
    "lmstudio",
    ProviderInfo(
        client_class=LMStudioClient,
        required_fields=["base_url"],
        optional_fields={"model": "", "timeout": 120.0},
        is_local=True,
    ),
)
