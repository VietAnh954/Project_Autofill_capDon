"""Persistent tracker for already-processed mail IDs (layer-2 anti-double).

Stores Outlook EntryIDs in data/state/processed_mail_ids.txt (one per line).
The MailFetcher is layer-1 (Unread filter); this is layer-2 for cases where
a mail was marked read but the pipeline crashed before moving it.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_STATE_FILE = Path("data/state/processed_mail_ids.txt")


class ProcessedTracker:
    """Read/write set of processed mail EntryIDs from a flat text file.

    Args:
        state_file: Path to the persistence file. Created on first write.
    """

    def __init__(self, state_file: Path = _DEFAULT_STATE_FILE) -> None:
        self._path = state_file
        self._ids: set[str] = self._load()

    def _load(self) -> set[str]:
        if not self._path.exists():
            return set()
        try:
            lines = self._path.read_text(encoding="utf-8").splitlines()
            return {line.strip() for line in lines if line.strip()}
        except Exception:
            logger.warning("tracker_load_failed", extra={"path": str(self._path)})
            return set()

    def is_processed(self, entry_id: str) -> bool:
        """Return True if this mail was already processed in a previous run."""
        return entry_id in self._ids

    def mark_processed(self, entry_id: str) -> None:
        """Record entry_id as processed and persist to disk immediately."""
        if entry_id in self._ids:
            return
        self._ids.add(entry_id)
        self._persist()

    def _persist(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                "\n".join(sorted(self._ids)) + "\n",
                encoding="utf-8",
            )
        except Exception:
            logger.error("tracker_persist_failed", extra={"path": str(self._path)}, exc_info=True)

    def __len__(self) -> int:
        return len(self._ids)
