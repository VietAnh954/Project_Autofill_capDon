"""Custom exceptions cho pipeline.

Xem CODING_RULES §4.
"""

from __future__ import annotations


class AutoFillError(Exception):
    """Base exception cho mọi lỗi business của pipeline."""


class MailFetchError(AutoFillError):
    """Lỗi khi fetch mail từ Outlook."""


class ReaderError(AutoFillError):
    """Lỗi khi đọc file attachment."""


class MappingError(AutoFillError):
    """Lỗi khi map field input → canonical."""


class ClassifierError(AutoFillError):
    """Không xác định được sheet đích."""


class ValidationError(AutoFillError):
    """Record không pass validate (required field thiếu, type sai)."""


class FillerError(AutoFillError):
    """Lỗi khi ghi vào file tổng."""


class DuplicateRecordError(AutoFillError):
    """Record trùng theo dedup key."""
