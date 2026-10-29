import os
from logging import Formatter
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT / ".env"
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Settings for the application"""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    log_level: str = Field(description="The log level", default="INFO")
    log_format: str = "[{levelname:^5}] {asctime} | ({filename}:{lineno}) | {message}"
    log_datefmt: str = "%H:%M:%S"
    log_style: str = "{"

    llm_provider: str = Field(description="The LLM provider", default="anthropic")
    llm_base_url: str
    llm_api_key: SecretStr
    llm_model: str
    llm_max_tokens: int = Field(default=4096)
    llm_timeout: int = Field(default=30)

    anthropic_version: str = Field(
        description="The Anthropic version", default="2026-10-21"
    )

    max_rounds: int = Field(
        description="The maximum number of rounds to run", default=3
    )
    db_path: Path = Field(
        description="SQLite path for conversation history",
        default=ROOT / ".data" / "conversations.db",
    )

    @model_validator(mode="before")
    @classmethod
    def bind_provider(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        provider = str(
            data.get("llm_provider") or os.getenv("LLM_PROVIDER") or "anthropic"
        ).lower()
        prefix = provider.upper()
        data["llm_provider"] = provider
        data.setdefault(
            "llm_base_url",
            os.getenv(f"{prefix}_BASE_URL", "https://api.anthropic.com/v1"),
        )
        data.setdefault("llm_api_key", os.getenv(f"{prefix}_API_KEY"))
        data.setdefault("llm_model", os.getenv(f"{prefix}_MODEL"))
        data.setdefault("llm_max_tokens", os.getenv(f"{prefix}_MAX_TOKENS") or 4096)
        return data

    @property
    def log_formatter(self) -> Formatter:
        return Formatter(
            fmt=self.log_format,
            datefmt=self.log_datefmt,
            style=self.log_style,
        )


settings = Settings()
