"""Gmail marker — danh dau mail da xu ly bang label "AutoFill/Processed".

Tuong duong voi marker.py nhung dung GmailClient.
"""

from __future__ import annotations

import logging

from auto_fill.mail.gmail_client import GmailClient
from auto_fill.mail.outlook_client import MailMessage

logger = logging.getLogger(__name__)

_PROCESSED_LABEL = "AutoFill/Processed"


def mark_gmail_processed(client: GmailClient, message: MailMessage) -> bool:
    """Them label Processed va xoa khoi UNREAD + INBOX.

    Returns
    -------
    bool
        True neu thanh cong, False neu loi.
    """
    try:
        label_id = client.get_or_create_label(_PROCESSED_LABEL)
        client.modify_labels(
            message.entry_id,
            add_labels=[label_id],
            remove_labels=["UNREAD", "INBOX"],
        )
        logger.info("Da danh dau Gmail message %s la Processed", message.entry_id)
        return True
    except Exception:
        logger.exception("Loi khi danh dau Gmail message %s", message.entry_id)
        return False
