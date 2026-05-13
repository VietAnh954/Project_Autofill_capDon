"""Pydantic settings — đọc cấu hình từ `.env`.

Mọi truy cập config trong codebase ĐI QUA module này.
KHÔNG dùng `os.environ` rải rác. Xem CODING_RULES §6.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Toàn bộ config dự án."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Paths ---
    master_file_path: Path
    data_root: Path
    log_dir: Path = Field(default=Path("logs"))

    # --- Outlook ---
    outlook_profile: str = "Outlook"
    outlook_inbox_folder: str = "Inbox"
    outlook_processed_folder: str = "Inbox\\Processed"

    # --- Sender ---
    sender_allowlist: str = ""  # comma-separated, parse trong property

    # --- Subject filter ---
    subject_pattern: str = r"(?i)c[aâ]p\s*[đd][oơ]n|phi[eế]u\s*c[aâ]p"

    # --- Behavior ---
    dry_run: bool = False
    backup_every_run: bool = False
    max_attachment_mb: int = 20
    retry_attempts: int = 3
    retry_delay_seconds: int = 10

    # --- Logging ---
    log_level: str = "INFO"
    log_json_path: Path = Path("logs/app.jsonl")

    @property
    def sender_allowlist_set(self) -> set[str]:
        """Trả về set các email allowed (lowercased)."""
        return {s.strip().lower() for s in self.sender_allowlist.split(",") if s.strip()}


# Singleton — import: `from auto_fill.config.settings import settings`
settings = Settings()  # type: ignore[call-arg]
