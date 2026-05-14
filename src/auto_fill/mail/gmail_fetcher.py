"""Gmail fetcher — filter email theo sender allowlist + subject pattern.

Tuong duong voi fetcher.py nhung dung GmailClient thay vi OutlookClient.
Tra ve cung kieu MailMessage de pipeline co the dung chung.
"""

from __future__ import annotations

import base64
import email
import logging
import re
from collections.abc import Iterator
from datetime import datetime
from email.header import decode_header
from typing import Any

from auto_fill.mail.gmail_client import GmailClient
from auto_fill.mail.outlook_client import MailMessage

logger = logging.getLogger(__name__)


class GmailFetcher:
    """Lay mail chua xu ly tu Gmail theo sender allowlist + subject regex.

    Parameters
    ----------
    client:
        GmailClient da connect().
    sender_allowlist:
        Set email duoc phep (lowercase). Rong = chap nhan tat ca.
    subject_pattern:
        Regex de loc subject. None = khong loc.
    max_results:
        So mail toi da lay trong 1 lan chay.
    """

    def __init__(
        self,
        client: GmailClient,
        sender_allowlist: set[str],
        subject_pattern: str | None = None,
        max_results: int = 50,
    ) -> None:
        self._client = client
        self._allowlist = {e.lower() for e in sender_allowlist}
        self._pattern = re.compile(subject_pattern, re.IGNORECASE) if subject_pattern else None
        self._max_results = max_results

    # ------------------------------------------------------------------ #

    def fetch(self) -> Iterator[MailMessage]:
        """Yield MailMessage cho moi mail match filter."""
        query_parts = ["is:unread", "has:attachment"]
        if self._allowlist:
            from_clause = " OR ".join(f"from:{e}" for e in sorted(self._allowlist))
            query_parts.append(f"({from_clause})")

        query = " ".join(query_parts)
        messages = self._client.list_messages(
            query=query,
            max_results=self._max_results,
            label_ids=["INBOX"],
        )
        logger.debug("Gmail query=%r returned %d messages", query, len(messages))

        for msg_meta in messages:
            msg_id = msg_meta["id"]
            try:
                full_msg = self._client.get_message(msg_id, fmt="full")
                mail = self._parse_message(msg_id, full_msg)
                if mail is None:
                    continue
                if not self._matches(mail):
                    continue
                yield mail
            except Exception:
                logger.exception("Loi khi xu ly Gmail message %s", msg_id)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _parse_message(self, msg_id: str, full: dict[str, Any]) -> MailMessage | None:
        headers = {
            h["name"].lower(): h["value"] for h in full.get("payload", {}).get("headers", [])
        }
        subject = _decode_header_value(headers.get("subject", ""))
        sender_raw = headers.get("from", "")
        sender_email = _extract_email(sender_raw)
        date_str = headers.get("date", "")
        received_at = _parse_date(date_str)

        # Attachment names
        attachment_names = _collect_attachment_names(full.get("payload", {}))

        body = _extract_body(full.get("payload", {}))

        return MailMessage(
            entry_id=msg_id,
            subject=subject,
            sender_email=sender_email,
            received_at=received_at,
            body=body,
            attachment_names=attachment_names,
        )

    def _matches(self, mail: MailMessage) -> bool:
        if self._allowlist and mail.sender_email.lower() not in self._allowlist:
            return False
        if self._pattern and not self._pattern.search(mail.subject):
            return False
        return True


# --------------------------------------------------------------------------- #
# Parsing helpers                                                              #
# --------------------------------------------------------------------------- #


def _decode_header_value(raw: str) -> str:
    parts = decode_header(raw)
    decoded_parts = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts)


def _extract_email(from_header: str) -> str:
    """'Nguyen Van A <abc@gmail.com>' → 'abc@gmail.com'."""
    match = re.search(r"<([^>]+)>", from_header)
    if match:
        return match.group(1).lower()
    return from_header.strip().lower()


def _parse_date(date_str: str) -> datetime:
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except Exception:
        return datetime.now()


def _collect_attachment_names(payload: dict[str, Any]) -> list[str]:
    names: list[str] = []
    parts = payload.get("parts", [])
    for part in parts:
        filename = part.get("filename", "")
        if filename:
            names.append(filename)
        # Recurse into nested parts
        names.extend(_collect_attachment_names(part))
    return names


def _extract_body(payload: dict[str, Any]) -> str:
    """Lay text/plain body tu payload (best-effort)."""
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        body = _extract_body(part)
        if body:
            return body
    return ""
