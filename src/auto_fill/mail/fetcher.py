"""Mail fetcher — lọc mail từ Outlook theo sender allowlist + subject pattern.

Tầng Mail trong pipeline (xem ARCHITECTURE.md mục 2).
Dùng OutlookClient để truy cập Outlook, sau đó áp filter.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator

from auto_fill.mail.outlook_client import MailMessage, OutlookClient

logger = logging.getLogger(__name__)


class MailFetcher:
    """Lọc mail mới từ Outlook theo sender allowlist và subject pattern.

    Args:
        client: OutlookClient đã connect().
        sender_allowlist: Set email được phép (lowercase). Rỗng = chấp nhận tất cả.
        subject_pattern: Regex pattern để lọc subject.
    """

    def __init__(
        self,
        client: OutlookClient,
        sender_allowlist: set[str],
        subject_pattern: str,
    ) -> None:
        self._client = client
        self._sender_allowlist = sender_allowlist
        self._subject_re = re.compile(subject_pattern, re.IGNORECASE)

    def fetch_matching(self) -> Iterator[MailMessage]:
        """Yield từng mail chưa đọc khớp với sender allowlist và subject pattern.

        Yields:
            MailMessage khớp cả 2 điều kiện filter.
        """
        total = 0
        matched = 0
        for msg in self._client.iter_unread():
            total += 1
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
