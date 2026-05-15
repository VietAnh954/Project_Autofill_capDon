"""Mail type classifier — decide A/B/C/D/review before processing.

Priority table (MAIL_PATTERNS.md §4):
  P10  D — body has status-report pattern (Tổng:/Trả:/Còn:)
  P20  C — subject CHECK PHƯƠNG ÁN + no Excel
  P30  B — GCN PDF attachment + subject confirms
  P40  A — Bill Ck / Bill confirm / Phí đã thanh toán + Excel
  P50  A — Thông tin tái tục / Thông tin cấp đơn + Excel
  P60  A — Cấp đơn mới / Gửi đơn + Excel
  P99  review — everything else
"""

from __future__ import annotations

import re

# P10 — TYPE D: status-report body (highest priority — even when xlsx is present)
RE_STATUS_REPORT = re.compile(
    r"(?i)(t[ổôố]ng\s*:?\s*\d+).{0,200}(tr[ảa]\s*ph[ưu][ơo]ng\s*[áa]n\s*:?\s*\d+).{0,200}(c[òo]n\s*:?\s*\d+)",
    re.DOTALL,
)

# P20 — TYPE C: check phương án discussion (no Excel required)
RE_CHECK_PA = re.compile(r"(?i)check\s*ph[ưu][ơo]ng\s*[áa]n")

# P30 — TYPE B: GCN PDF from insurer
RE_GCN_SUBJECT = re.compile(
    r"(?i)(x[áa]c\s*nh[âậ]n\s*ph[ưu][ơo]ng\s*[áa]n|gcn|gi[âấ]y\s*ch[ưứ]ng\s*nh[âậ]n)"
)
RE_GCN_FILENAME = re.compile(r"^GCN\s+.+\.pdf$", re.IGNORECASE)

# P40-P60 — TYPE A: new policy / bill confirm (all sub-priorities return 'A')
RE_NEW_POLICY = re.compile(
    "(?i)("
    # P40
    "bill\\s*ck|"
    "bill\\s*confirm|"
    "ph[íi]\\s*[đdã]ã?\\s*thanh\\s*to[áa]n|"
    # P50
    "th[oô]ng\\s*tin\\s*t[áaấ]i\\s*t[uụ]c|"
    "th[oô]ng\\s*tin\\s*c[áaấ]p\\s*[đd][ơo]n|"
    # P60
    "c[áaấ]p\\s*[đd][ơo]n\\s*m[ơớo]i|"
    "g[ưửữ]i\\s*[đd][ơo]n"
    ")"
)


def classify_mail_type(subject: str, body: str, attachments: list[str]) -> str:
    """Classify a mail into one of: 'A', 'B', 'C', 'D', 'review'.

    Args:
        subject: Top-level subject line of the mail.
        body: Top-level body text (pre-stripped of reply quotes).
        attachments: List of attachment filenames (basename only).

    Returns:
        Single character string: 'A' | 'B' | 'C' | 'D' | 'review'.
    """
    # P10
    if RE_STATUS_REPORT.search(body):
        return "D"

    has_excel = any(a.lower().endswith((".xlsx", ".xls", ".csv")) for a in attachments)
    has_gcn_pdf = any(RE_GCN_FILENAME.match(a) for a in attachments)

    # P20
    if RE_CHECK_PA.search(subject) and not has_excel:
        return "C"

    # P30
    if has_gcn_pdf and RE_GCN_SUBJECT.search(subject):
        return "B"

    # P40-P60
    if has_excel and RE_NEW_POLICY.search(subject):
        return "A"

    return "review"
