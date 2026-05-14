"""Pydantic settings — đọc cấu hình từ `.env`.

Mọi truy cập config trong codebase ĐI QUA module này.
KHÔNG dùng `os.environ` rải rác. Xem CODING_RULES §6.

Note: default value cho các Path là relative tới project root, dùng được khi
chưa có `.env`. Khi production, BẮT BUỘC override qua `.env` (xem `.env.example`).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = parent của src/auto_fill/config/settings.py 3 cấp lên.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Toàn bộ config dự án."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Paths (có default để import không fail khi chưa có .env) ---
    master_file_path: Path = Field(default=_PROJECT_ROOT / "data" / "master" / "master.xlsx")
    data_root: Path = Field(default=_PROJECT_ROOT / "data")
    log_dir: Path = Field(default=_PROJECT_ROOT / "logs")
    db_path: Path = Field(default=_PROJECT_ROOT / "data" / "db" / "autofill.db")

    # --- Outlook ---
    outlook_profile: str = "Outlook"
    outlook_inbox_folder: str = "Inbox"
    outlook_processed_folder: str = "Inbox\\Processed"

    # --- Sender ---
    sender_allowlist: str = ""  # comma-separated, parse trong property

    # --- Subject filter ---
    subject_pattern: str = r"(?i)c[aâấ]p\s*[đd][oơô]n|phi[eếề]u\s*c[aâấ]p"

    # --- Behavior ---
    dry_run: bool = False
    backup_every_run: bool = False
    max_attachment_mb: int = 20
    retry_attempts: int = 3
    retry_delay_seconds: int = 10
    db_enabled: bool = True  # ghi vao SQLite khi True

    # --- Gmail (tuy chon) ---
    gmail_credentials_file: Path | None = None  # credentials.json tu Google Cloud Console
    gmail_token_file: Path | None = None  # token.json (tu dong tao sau oauth flow)

    # --- Cloud / Postgres (tuy chon) ---
    # Khi set, DATABASE_URL ghi de db_path cho toan bo SQLAlchemy.
    # Format: postgresql+psycopg2://user:pass@host:5432/dbname
    database_url: str | None = None

    # --- Logging ---
    log_level: str = "INFO"
    log_json_path: Path = Field(default=_PROJECT_ROOT / "logs" / "app.jsonl")

    @property
    def sender_allowlist_set(self) -> set[str]:
        """Trả về set các email allowed (lowercased)."""
        return {s.strip().lower() for s in self.sender_allowlist.split(",") if s.strip()}


# Singleton — import: `from auto_fill.config.settings import settings`
settings = Settings()
