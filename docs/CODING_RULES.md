# CODING_RULES.md

> Quy tắc viết code cho mọi file Python trong dự án.
> Claude PHẢI đọc file này TRƯỚC khi viết hay sửa code.

---

## 1. Language & Version

- **Python 3.11+** (vì có `tomllib`, `Self`, exception groups).
- Type hint BẮT BUỘC cho mọi function public.
- Format: **black** + **ruff** (xem `pyproject.toml`).

---

## 2. Naming convention

| Đối tượng | Quy ước | Ví dụ |
|-----------|---------|-------|
| File / module | `snake_case.py` | `outlook_client.py` |
| Class | `PascalCase` | `OutlookClient` |
| Function / variable | `snake_case` | `fetch_new_mails` |
| Constant | `UPPER_SNAKE` | `MAX_RETRY = 3` |
| Private | prefix `_` | `_parse_subject` |
| Test file | `test_<module>.py` | `test_classifier.py` |
| Tiếng Việt | KHÔNG dùng cho identifier | dùng `customer_name` không phải `ten_kh` |

---

## 3. Cấu trúc file Python chuẩn

```python
"""Mô tả module (1 dòng).

Mô tả dài hơn nếu cần. Đề cập module này nằm ở tầng nào trong pipeline
(xem ARCHITECTURE.md mục 2).
"""

from __future__ import annotations

# 1. stdlib
import logging
from pathlib import Path

# 2. third-party
import pandas as pd
from openpyxl import load_workbook

# 3. local
from auto_fill.config.settings import Settings
from auto_fill.utils.paths import ensure_dir

logger = logging.getLogger(__name__)

# === Constants ===
MAX_ROWS_PER_BATCH = 500

# === Public API ===
def read_excel_attachment(path: Path) -> pd.DataFrame:
    """Đọc 1 file Excel attachment, trả về DataFrame chuẩn nội bộ.

    Args:
        path: đường dẫn tới file .xlsx trong data/inbox/.

    Returns:
        DataFrame với cột theo MAPPING.md mục "Internal canonical fields".

    Raises:
        FileNotFoundError: nếu path không tồn tại.
        ValueError: nếu file không match format kỳ vọng.
    """
    ...

# === Private helpers ===
def _detect_header_row(...) -> int:
    ...
```

---

## 4. Error handling

- **KHÔNG bao giờ `except: pass`.** Tối thiểu phải `logger.exception()`.
- Custom exception trong `src/auto_fill/utils/errors.py`:
  - `MailFetchError`, `ReaderError`, `MappingError`, `FillerError`.
- Lỗi business → raise custom exception; lỗi system (IO, network) → để bubble.
- Retry với `tenacity` cho lỗi network / COM, KHÔNG retry cho lỗi validate.

---

## 5. Logging

- Dùng `logging.getLogger(__name__)`, KHÔNG dùng `print()`.
- Level: `DEBUG` chi tiết flow, `INFO` mỗi step pipeline, `WARNING` skip / retry,
  `ERROR` fail rõ ràng, `CRITICAL` cần dừng app.
- Output: console + file `logs/app.jsonl` (JSON line format).
- KHÔNG log credential, KHÔNG log nội dung CCCD/CMND đầy đủ — chỉ log 4 ký tự cuối.

```python
logger.info("processed_mail", extra={"msg_id": mid, "sheet": "Du lịch", "rows": 12})
```

---

## 6. Config & secrets

- Tất cả config qua `pydantic-settings` trong `src/auto_fill/config/settings.py`.
- File `.env` ở root, KHÔNG commit. Template ở `.env.example`.
- Truy cập: `from auto_fill.config import settings`. KHÔNG `os.environ[...]` rải rác.

---

## 7. I/O với file Excel tổng

- Luôn `backup` trước khi mở chế độ ghi (xem ARCHITECTURE §3.4).
- Mở: `load_workbook(path, data_only=False, keep_vba=False)` để giữ formula.
- Lưu vào path mới trong `data/processed/`, KHÔNG ghi đè gốc trừ khi user override.
- KHÔNG `del ws[row]`. Append-only.

---

## 8. Testing

- Framework: **pytest**.
- Tối thiểu 1 unit test / public function.
- Fixture file Excel mẫu nhỏ ở `tests/fixtures/`, KHÔNG dùng file thật.
- Smoke test end-to-end ở `tests/test_pipeline_smoke.py`.
- Lệnh: `pytest -q` phải xanh trước khi commit.

---

## 9. Git workflow

### Branch
- `main`: stable.
- `feat/<task-id>-<short-name>`: cho mỗi task trong TODO.md.
- `fix/<bug-short-name>`.

### Commit message (Conventional Commits)
```
<type>(<scope>): <subject>

<body — optional>
<footer — optional, refs TODO task ID>
```

Type: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`.

Ví dụ:
```
feat(mail): fetch unread mails matching subject pattern

Implements outlook_client.fetch_new_mails(). Filters by configured
sender allowlist. Returns iterator of MailMessage dataclass.

Refs: TODO #1.2
```

### Pull / merge
- 1 task = 1 commit hoặc rebase squash. Tránh commit "wip".

---

## 10. Docstring style

- Google-style (như ví dụ mục 3). KHÔNG NumPy / reST style.

---

## 11. Performance guardrails

- File tổng > 10MB → KHÔNG load toàn bộ vào RAM khi chỉ append.
  Dùng `read_only=True` để scan, `write_only=False` để append.
- Tránh `pd.concat` trong vòng lặp → collect list rồi `pd.DataFrame(list)`.

---

## 12. Anti-patterns (KHÔNG được làm)

- ❌ Mutable default argument: `def f(x=[]):`
- ❌ Catch `Exception` ở top-level rồi nuốt.
- ❌ Import vòng module-level (dùng deferred import nếu cần).
- ❌ Magic number không tên — đặt constant.
- ❌ Đặt tên biến `data`, `result`, `temp` — phải mô tả.
- ❌ Hardcode đường dẫn tuyệt đối Windows — dùng `Path` + `settings`.

---

## 13. Pre-commit hook (sẽ setup ở Phase 0)

```yaml
# .pre-commit-config.yaml
- ruff check
- ruff format
- mypy src/
- pytest -q --no-header
```

Claude phải chạy `pre-commit run --all-files` trước khi commit.
