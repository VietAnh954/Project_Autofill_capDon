"""Strip nested reply quotes from email body — keep only top-level content.

Strategy (MAIL_PATTERNS.md §5.1):
  Find the first occurrence of an email-quote header line
  ("From:", "Sent:", "Subject:", or Vietnamese/Outlook equivalents)
  that looks like the start of a quoted section, then truncate body there.
"""

from __future__ import annotations

import re

# Common quote-header patterns from Outlook/Gmail (EN + VI)
_QUOTE_HEADER = re.compile(
    r"^-{2,}.*-{2,}$"  # "---- Original Message ----" or "-----..."
    r"|^_{3,}$"  # "___________"
    r"|^From\s*:",
    re.IGNORECASE | re.MULTILINE,
)

# Outlook-style quoted block: "On <date>, <name> wrote:"
_ON_DATE_WROTE = re.compile(
    r"^On\s+.{5,100}wrote\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Vietnamese Outlook: "Từ:", "Gửi:", "Đến:", "Chủ đề:" all on consecutive lines
_VI_QUOTE_BLOCK = re.compile(
    r"^(Từ|Gửi|T[ừu]:|G[ửu]i:)\s*:",
    re.IGNORECASE | re.MULTILINE,
)

# Inline ">" citation lines (RFC 2822)
_ANGLE_QUOTE_LINE = re.compile(r"^>", re.MULTILINE)


def strip_reply_quotes(body: str) -> str:
    """Return only the top-level text of an email body.

    Removes everything from the first quoted-section header onward.
    Lines starting with ">" (inline citations) are also removed.

    Args:
        body: Raw email body text (plain-text or lightly-HTML-stripped).

    Returns:
        Trimmed top-level body text with trailing whitespace removed.
    """
    cut_at = len(body)

    for pattern in (_QUOTE_HEADER, _ON_DATE_WROTE, _VI_QUOTE_BLOCK):
        match = pattern.search(body)
        if match and match.start() < cut_at:
            cut_at = match.start()

    top = body[:cut_at]

    # Remove any inline "> " citation lines that slipped through
    top = "\n".join(line for line in top.splitlines() if not _ANGLE_QUOTE_LINE.match(line))

    return top.strip()
