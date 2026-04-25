from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, model_validator

load_dotenv()

# Phase 1 supports local providers only.
# Phase 2 will expand this literal as each cloud client is implemented.
_PHASE1_PROVIDERS = ("ollama", "lmstudio")
_CLOUD_PROVIDERS = ("anthropic", "openai", "gemini", "groq", "mistral")


class Settings(BaseModel):
    llm_provider: Literal["ollama", "lmstudio"] = "ollama"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # LM Studio
    lmstudio_base_url: str = "http://localhost:1234"
    lmstudio_model: str = ""

    # Campaigns — root directory that contains all campaign sub-folders.
    # CAMPAIGN_FOLDER (optional) sets the campaign selected on first launch.
    campaigns_root: str
    campaign_folder: str = ""  # empty = user picks from the UI

    # Storage
    database_path: str = "./sessions.db"

    @field_validator("llm_provider", mode="before")
    @classmethod
    def _normalize_provider(cls, v: str) -> str:
        normalised = v.strip().lower()
        if normalised in _CLOUD_PROVIDERS:
            raise ValueError(
                f"LLM_PROVIDER '{normalised}' is a cloud provider and is not yet "
                "supported in Phase 1. Use 'ollama' (default) or 'lmstudio'. "
                "Cloud providers will be enabled in Phase 2."
            )
        return normalised

    @model_validator(mode="after")
    def _validate_provider_config(self) -> "Settings":
        if self.llm_provider == "ollama":
            if not self.ollama_base_url:
                raise ValueError("OLLAMA_BASE_URL must not be empty.")
            if not self.ollama_model:
                raise ValueError("OLLAMA_MODEL must not be empty.")
        elif self.llm_provider == "lmstudio":
            if not self.lmstudio_base_url:
                raise ValueError("LMSTUDIO_BASE_URL must not be empty.")
        return self

    @field_validator("campaigns_root", mode="after")
    @classmethod
    def _validate_campaigns_root(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "CAMPAIGNS_ROOT is required. "
                "Set it to the absolute path of the folder containing your campaign sub-folders."
            )
        if not os.path.isdir(v):
            raise ValueError(
                f"CAMPAIGNS_ROOT '{v}' does not exist or is not a directory."
            )
        return v

    @field_validator("campaign_folder", mode="after")
    @classmethod
    def _validate_campaign_folder(cls, v: str) -> str:
        # Optional — empty means the user will pick from the UI.
        if v and not os.path.isdir(v):
            raise ValueError(
                f"CAMPAIGN_FOLDER '{v}' does not exist or is not a directory."
            )
        return v


def load_settings() -> Settings:
    """Load and validate settings from environment variables.

    Raises SystemExit with a human-readable message on misconfiguration so that
    callers (including Streamlit) get a clear error rather than a raw exception.
    """
    try:
        return Settings(
            llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            lmstudio_base_url=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234"),
            lmstudio_model=os.getenv("LMSTUDIO_MODEL", ""),
            campaigns_root=os.getenv("CAMPAIGNS_ROOT", ""),
            campaign_folder=os.getenv("CAMPAIGN_FOLDER", ""),
            database_path=os.getenv("DATABASE_PATH", "./sessions.db"),
        )
    except Exception as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc
