from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, model_validator

load_dotenv()


class Settings(BaseModel):
    llm_provider: Literal["anthropic", "ollama"] = "anthropic"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-5"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Campaign
    campaign_folder: str

    # Storage
    database_path: str = "./sessions.db"

    @field_validator("llm_provider", mode="before")
    @classmethod
    def _normalize_provider(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def _validate_provider_credentials(self) -> "Settings":
        if self.llm_provider == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic. "
                    "Set it in your .env file or environment."
                )
        elif self.llm_provider == "ollama":
            if not self.ollama_base_url:
                raise ValueError(
                    "OLLAMA_BASE_URL is required when LLM_PROVIDER=ollama."
                )
            if not self.ollama_model:
                raise ValueError(
                    "OLLAMA_MODEL is required when LLM_PROVIDER=ollama."
                )
        else:
            raise ValueError(
                f"Unsupported LLM_PROVIDER '{self.llm_provider}'. "
                "Supported values: anthropic, ollama."
            )
        return self

    @field_validator("campaign_folder", mode="after")
    @classmethod
    def _validate_campaign_folder(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "CAMPAIGN_FOLDER is required. "
                "Set it to the absolute path of your campaign folder in .env."
            )
        if not os.path.isdir(v):
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
            llm_provider=os.getenv("LLM_PROVIDER", "anthropic"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3"),
            campaign_folder=os.getenv("CAMPAIGN_FOLDER", ""),
            database_path=os.getenv("DATABASE_PATH", "./sessions.db"),
        )
    except Exception as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc
