"""Mail type classifier — decide A/B/C/D/review before processing.

Decision tree (MAIL_PATTERNS.md §3):
  D → body has status report pattern
  B → GCN PDF attachment + subject confirms
  A → Excel attachment + TYPE A subject
  C → CHECK PHƯƠNG ÁN + no Excel
  review → everything else
"""

from __future__ import annotations

import re

# TYPE D: status-report body (highest priority — even when xlsx is present)
RE_STATUS_REPORT = re.compile(
    r"(?i)(t[ổôố]ng\s*:?\s*\d+).{0,200}(tr[ảa]\s*ph[ưu][ơo]ng\s*[áa]n\s*:?\s*\d+).{0,200}(c[òo]n\s*:?\s*\d+)",
    re.DOTALL,
)

# TYPE C: check phương án discussion
RE_CHECK_PA = re.compile(r"(?i)check\s*ph[ưu][ơo]ng\s*[áa]n")

# TYPE A: cấp đơn / bill confirm
RE_NEW_POLICY = re.compile(
    "(?i)("
    "th[oô]ng\\s*tin\\s*t[áaấ]i\\s*t[uụ]c|"
    "th[oô]ng\\s*tin\\s*c[áaấ]p\\s*[đd][ơo]n|"
    "bill\\s*ck|"
    "ph[íi]\\s*[đdã]ã?\\s*thanh\\s*to[áa]n|"
    "c[áaấ]p\\s*[đd][ơo]n\\s*m[ơớo]i|"
    "g[ưửữ]i\\s*[đd][ơo]n"
    ")"
)

# TYPE B: GCN from insurer
RE_GCN_SUBJECT = re.compile(
    r"(?i)(x[áa]c\s*nh[âậ]n\s*ph[ưu][ơo]ng\s*[áa]n|gcn|gi[âấ]y\s*ch[ưứ]ng\s*nh[âậ]n)"
)
RE_GCN_FILENAME = re.compile(r"^GCN\s+.+\.pdf$", re.IGNORECASE)


def classify_mail_type(subject: str, body: str, attachments: list[str]) -> str:
    """Classify a mail into one of: 'A', 'B', 'C', 'D', 'review'.

    Args:
        subject: Top-level subject line of the mail.
        body: Top-level body text (pre-stripped of reply quotes).
        attachments: List of attachment filenames (basename only).

    Returns:
        Single character string: 'A' | 'B' | 'C' | 'D' | 'review'.
    """
    if RE_STATUS_REPORT.search(body):
        return "D"

    has_excel = any(a.lower().endswith((".xlsx", ".xls", ".csv")) for a in attachments)
    has_gcn_pdf = any(RE_GCN_FILENAME.match(a) for a in attachments)

    if has_gcn_pdf and RE_GCN_SUBJECT.search(subject):
        return "B"

    if has_excel and RE_NEW_POLICY.search(subject):
        return "A"

    if RE_CHECK_PA.search(subject) and not has_excel:
        return "C"

    return "review"
