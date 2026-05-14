"""Gui bao cao qua Outlook — dung pywin32 COM.

Yeu cau: Outlook Desktop dang chay. Xem mail/outlook_client.py.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def send_report_email(
    report_path: Path,
    recipients: list[str],
    subject: str | None = None,
    namespace: Any = None,
) -> bool:
    """Gui file report qua Outlook.

    Args:
        report_path: Duong dan toi file .md da render.
        recipients: Danh sach dia chi email nhan.
        subject: Tieu de email (mac dinh tu ten file).
        namespace: Outlook MAPI namespace (de test co the inject mock).

    Returns:
        True neu gui thanh cong, False neu fail (khong raise de tranh dung pipeline).
    """
    if not report_path.exists():
        logger.error("report_file_not_found", extra={"path": str(report_path)})
        return False

    if not recipients:
        logger.warning("no_recipients_for_report")
        return False

    try:
        if namespace is None:
            import win32com.client as win32

            outlook = win32.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            namespace.Logon()

        mail = namespace.Application.CreateItem(0)
        mail.Subject = subject or f"[Auto] {report_path.stem}"
        mail.Body = report_path.read_text(encoding="utf-8")
        mail.To = "; ".join(recipients)
        mail.Attachments.Add(str(report_path.resolve()))
        mail.Send()

        logger.info(
            "report_sent",
            extra={"recipients": recipients, "subject": mail.Subject},
        )
        return True

    except Exception as exc:
        logger.error("report_send_failed", extra={"error": str(exc)})
        return False
