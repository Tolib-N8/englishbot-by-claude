from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root: parents[2] = repo root (backend/app/config.py -> backend/app -> backend -> repo)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Using Claude Agent SDK with local Pro/Max subscription — no API key.
    # Model selection is delegated to the SDK / Claude Code; leave as None
    # to use whatever model Claude Code is currently configured to use.
    claude_model: str | None = None

    database_url: str = f"sqlite+aiosqlite:///{DATA_DIR}/data.db"
    backend_cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    user_level: str = "A1"
    user_native_language: str = "ru"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


settings = Settings()
