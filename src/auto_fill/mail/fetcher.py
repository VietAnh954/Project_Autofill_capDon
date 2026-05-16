"""Mail fetcher — lọc mail từ Outlook theo sender allowlist + subject pattern.

Tầng Mail trong pipeline (xem ARCHITECTURE.md mục 2).
Dùng OutlookClient để truy cập Outlook, sau đó áp filter.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator

from auto_fill.mail.outlook_client import MailMessage, OutlookClient
from auto_fill.mail.processed_tracker import ProcessedTracker

logger = logging.getLogger(__name__)


class MailFetcher:
    """Lọc mail mới từ Outlook theo sender allowlist và subject pattern.

    Args:
        client: OutlookClient đã connect().
        sender_allowlist: Set email được phép (lowercase). Rỗng = chấp nhận tất cả.
        subject_pattern: Regex pattern để lọc subject.
        target_folder: Subfolder path relative to inbox to scan.
            Defaults to "AutoFill/Incoming". Falls back to inbox if not found.
            Pass None to scan default inbox directly.
    """

    def __init__(
        self,
        client: OutlookClient,
        sender_allowlist: set[str],
        subject_pattern: str,
        target_folder: str | None = "AutoFill/Incoming",
        tracker: ProcessedTracker | None = None,
        include_read: bool = False,
    ) -> None:
        self._client = client
        self._sender_allowlist = sender_allowlist
        self._subject_re = re.compile(subject_pattern, re.IGNORECASE)
        self._target_folder = target_folder
        self._tracker = tracker or ProcessedTracker()
        self._include_read = include_read

    def fetch_matching(self) -> Iterator[MailMessage]:
        """Yield mail khớp với sender allowlist và subject pattern.

        Mặc định chỉ lấy mail chưa đọc. Khi include_read=True, lấy cả mail đã đọc
        (hữu ích để test / reprocess).

        Scans AutoFill/Incoming subfolder; falls back to default inbox when the
        subfolder does not exist (logged as warning by OutlookClient).

        Yields:
            MailMessage khớp cả 2 điều kiện filter.
        """
        total = 0
        matched = 0
        folder = self._client.resolve_folder(self._target_folder)
        iter_fn = self._client.iter_all if self._include_read else self._client.iter_unread
        for msg in iter_fn(folder=folder):
            total += 1
            if self._tracker.is_processed(msg.entry_id):
                logger.debug(
                    "skip_already_processed",
                    extra={"entry_id": msg.entry_id[:8], "subject": msg.subject[:40]},
                )
                continue
            if not self._is_sender_allowed(msg.sender_email):
                logger.debug(
                    "skip_sender",
                    extra={"sender": msg.sender_email, "subject": msg.subject[:40]},
                )
                continue
            if not self._is_subject_match(msg.subject):
                logger.debug(
                    "skip_subject",
                    extra={"sender": msg.sender_email, "subject": msg.subject[:40]},
                )
                continue
            matched += 1
            logger.info(
                "mail_matched",
                extra={
                    "sender": msg.sender_email,
                    "subject": msg.subject[:60],
                    "received": msg.received_at.isoformat(),
                },
            )
            yield msg

        logger.info("fetch_done", extra={"total_unread": total, "matched": matched})

    def _is_sender_allowed(self, sender_email: str) -> bool:
        """Trả True nếu sender allowlist rỗng hoặc email có trong list."""
        if not self._sender_allowlist:
            return True
        return sender_email.lower() in self._sender_allowlist

    def _is_subject_match(self, subject: str) -> bool:
        """Trả True nếu subject khớp với pattern."""
        return bool(self._subject_re.search(subject))
