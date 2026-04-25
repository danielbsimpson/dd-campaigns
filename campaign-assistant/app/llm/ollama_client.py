from __future__ import annotations

import shutil
import subprocess
import httpx

from .base import BaseLLMClient, LLMError, ProviderInfo, register_provider


class OllamaClient(BaseLLMClient):
    """LLM client for a locally running Ollama server."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._timeout = timeout

    # ------------------------------------------------------------------
    # BaseLLMClient interface
    # ------------------------------------------------------------------

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.ConnectError:
            raise LLMError(
                "Cannot connect to Ollama. Make sure Ollama is running "
                f"at {self.base_url}. Start it with: ollama serve"
            )
        except httpx.TimeoutException:
            raise LLMError(
                f"Ollama request timed out after {self._timeout}s. "
                "The model may still be loading — try again in a moment."
            )
        except httpx.HTTPStatusError as exc:
            raise LLMError(
                f"Ollama returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:300]}"
            )

        data = response.json()
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMError(f"Unexpected Ollama response format: {data}") from exc

    def list_models(self) -> list[str]:
        """Return model tags currently available in Ollama."""
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def detect_gpu(self) -> bool | None:
        """Return True if an NVIDIA GPU with CUDA is available on this machine.

        Strategy:
        1. Try Ollama's ``/api/ps`` endpoint — if a model is currently loaded
           and ``size_vram > 0`` it is running on the GPU.
        2. Fall back to checking whether ``nvidia-smi`` is on PATH (means CUDA
           drivers are installed, so Ollama will use the GPU).
        Returns None if neither check is conclusive.
        """
        # ── Check /api/ps first (only useful when a model is loaded) ─────
        try:
            response = httpx.get(f"{self.base_url}/api/ps", timeout=5.0)
            if response.is_success:
                data = response.json()
                for model in data.get("models", []):
                    if model.get("size_vram", 0) > 0:
                        return True
        except Exception:
            pass

        # ── Fall back to nvidia-smi presence ─────────────────────────────
        if shutil.which("nvidia-smi") is not None:
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return True
            except Exception:
                pass

        return False


# ---------------------------------------------------------------------------
# Register with the provider registry
# ---------------------------------------------------------------------------

register_provider(
    "ollama",
    ProviderInfo(
        client_class=OllamaClient,
        required_fields=["base_url", "model"],
        optional_fields={"timeout": 120.0},
        is_local=True,
    ),
)
