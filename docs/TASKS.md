# TASKS.md — Active Task Log

> Nhật ký trạng thái task hiện tại + open questions.
> Claude update file này SAU KHI hoàn thành mỗi task trong TODO.md.

---

## Đang làm

Phase 7 — Task 7.2 (email_quote.py) kế tiếp.

---

## Session Summary — 2026-05-16 (Phase 7: Mail Pattern Refinement)

| Task | File chính | Tests | Trạng thái |
|------|-----------|-------|-----------|
| 7.1 skip_filter | `mapper/skip_filter.py` | 22 passed | ✅ |
| 7.2 email_quote | `mapper/email_quote.py` | 14 passed | ✅ |

**Full test suite: 488 passed**

### Chi tiết 7.1:
- `classify_mail_type(subject, body, attachments)` → 'A'/'B'/'C'/'D'/'review'
- Priority: D (body status report) > B (GCN PDF) > A (Excel + subject) > C (CHECK PHƯƠNG ÁN, no excel) > review
- Fix regex Unicode: `c[áaấ]p`, `m[ơớo]i` để match full diacritics như "Cấp đơn mới"
- 4 mail mẫu pass đúng: mail1=C, mail2=A, mail3=B, mail4=B

---

## Session Summary — 2026-05-14 (Phase 6: Dashboard + Gmail)

**Phase 6: Web Dashboard (daily-use) + Gmail source**

| Task | File chính | Tests | Trạng thái |
|------|-----------|-------|-----------|
| 6.1 pipeline_state | `api/pipeline_state.py` | — | ✅ |
| 6.2 API endpoints | `api/app.py` (pipeline/run, status, logs/stream) | 12 passed | ✅ |
| 6.3 Jinja2 setup | `api/app.py` | — | ✅ |
| 6.4 HTML templates | `api/templates/base.html`, `dashboard.html`, `records.html` | — | ✅ |
| 6.5 Dashboard tests | `tests/test_dashboard_routes.py` | 12 passed | ✅ |
| 6.6 GmailClient | `mail/gmail_client.py` | — | ✅ |
| 6.7 GmailFetcher | `mail/gmail_fetcher.py` | — | ✅ |
| 6.8 GmailDownloader + Marker | `mail/gmail_downloader.py`, `mail/gmail_marker.py` | 12 passed | ✅ |
| 6.9 --source flag | `__main__.py` (run cmd + gmail-setup cmd) | — | ✅ |
| 6.10 Gmail tests | `tests/test_gmail_client.py` | 12 passed | ✅ |
| 6.11 requirements.txt | jinja2, python-multipart, google libs | — | ✅ |

**Full test suite: 452 passed**

### Dashboard features:
- `/dashboard` — stats cards (6 sheet + tổng), pipeline control (Chạy/Dry Run), live log console (SSE), recent records
- `/dashboard/records` — filter theo sheet/ngày/tên, paginate, export Excel
- `/` → redirect `/dashboard`

### Gmail features:
- `GmailClient`: OAuth2 PKCE, list messages, get attachment, modify labels
- `GmailFetcher`: filter sender allowlist + subject regex, reuse `MailMessage` dataclass
- `GmailDownloader`: tải xlsx/csv/pdf vào data/inbox/
- `GmailMarker`: thêm label "AutoFill/Processed", xóa UNREAD/INBOX
- CLI: `python -m auto_fill run --source gmail|outlook|both`
- CLI: `python -m auto_fill gmail-setup` — OAuth2 setup flow

### Note kỹ thuật:
- Starlette 1.0.0 dùng API mới: `TemplateResponse(request, name, context)` (bỏ API cũ)
- SSE test không stream thực (infinite generator) — dùng mock/state check thay

---

## Session Summary — 2026-05-14 (Phase 5 hoàn thành)

**Phase 5: Documentation Website — GitHub Pages**

| Task | Mô tả | Trạng thái |
|------|-------|-----------|
| 5.1 | Cài mkdocs-material, glightbox, mermaid2 | ✅ |
| 5.2 | Viết mkdocs.yml | ✅ |
| 5.3 | Tạo site_docs/ (7 trang) | ✅ |
| 5.4 | Test local mkdocs serve | ✅ |
| 5.5 | GitHub Actions deploy-docs.yml | ✅ |
| 5.6 | Enable GitHub Pages (user tay) | ✅ |
| 5.7 | Custom domain | ✅ skipped (không có domain) |
| 5.8 | Tag v0.5.0-docs-site | ✅ |

Site live tại: https://vietanh954.github.io/Project_Autofill_capDon/

---

## Session Summary — 2026-05-14 (Phase 4 task 4.1)

**Task 4.1: Đóng gói Windows service (NSSM).**

| Task | File chính | Tests | Commit |
|------|-----------|-------|--------|
| 4.1 Windows Service | `scripts/install_service.ps1`, `scripts/uninstall_service.ps1`, `src/auto_fill/windows_service.py` | 10 passed | `ecac87f` |
| 4.2 GUI Tkinter | `src/auto_fill/gui.py`, `__main__.py` (gui command) | 10 passed | `030f05a` |
| 4.3 Postgres/cloud | `db/engine.py`, `config/settings.py`, `alembic/env.py`, `tools/push_to_postgres.py` | 6 passed | `5b6a3e7` |
| 4.4 FastAPI | `src/auto_fill/api/` (app.py, schemas.py, __init__.py), `__main__.py` (serve cmd) | 14 passed | `f42d907` |
| 5.1-5.5 Docs site | `mkdocs.yml`, `site_docs/`, `.github/workflows/deploy-docs.yml` | build OK | — |

### Chi tiết:
- `scripts/install_service.ps1` — PowerShell script dùng NSSM cài service; cấu hình AppDirectory, log rotation, auto-start, description.
- `scripts/uninstall_service.ps1` — dừng + xóa service, có confirm prompt.
- `src/auto_fill/windows_service.py` — pywin32 native service wrapper; `_WIN32_AVAILABLE` guard cho phép test không cần admin; `SvcStop` signal stop event; `_run()` loop với WaitForSingleObject interval.
- `tests/test_windows_service.py` — 10 tests: constants, main() exit khi no win32, main() dispatch với mock win32, class attributes, SvcStop behavior.

---

## Session Summary — 2026-05-14 (Phase 3 hoàn thành)

**Session này hoàn thành toàn bộ Phase 3 Database (task 3.1 → 3.6).**

### Tasks đã làm trong session này:

| Task | File chính | Tests | Commit |
|------|-----------|-------|--------|
| 3.1 SQLite schema | `db/models.py`, `db/engine.py`, `settings.py` | 14 passed | `819d1d1` |
| 3.2 Alembic init | `alembic/`, `alembic.ini`, `alembic/env.py` | migration verified | `728ceef` |
| 3.3 Migration script | `tools/migrate_excel_to_sqlite.py` | 11 passed | `7cac572` |
| 3.4 Dual-write pipeline | `db/repository.py`, `filler/db_exporter.py`, `__main__.py` | 14 passed | `d1fc3ae` |
| 3.5 CLI export | `__main__.py` (export_cmd) | 4 passed | `6ee4d48` |
| 3.6 Tag v0.3.0 | — | — | tag pushed |

### Trạng thái repo:
- Branch: `main`
- Tag: `v0.3.0` (pushed)
- Full test suite: 388 passed

---

## Session Summary — 2026-05-14 (Phase 2 hoàn thành)

**Session này hoàn thành toàn bộ Phase 2 mở rộng 6 sheet (task 2.1 → 2.9).**

### Tasks đã làm trong session này:

| Task | File chính | Tests | Commit |
|------|-----------|-------|--------|
| 2.1 Classifier 6 sheets | `mapper/classifier.py`, `config/sheet_registry.py` | passed | — |
| 2.2 Mapping table | `mapper/sheet_mapping.py` | passed | — |
| 2.3 aliases.yaml đầy đủ | `mapper/aliases.yaml`, `aliases_loader.py` | passed | — |
| 2.4 PDF reader | `reader/pdf_reader.py` | passed | — |
| 2.5 PDF OCR fallback | `reader/ocr_reader.py` | passed | — |
| 2.6 Report + Outlook sender | `reporter/daily_report.py`, `reporter/outlook_sender.py` | passed | — |
| 2.7 Scheduler | `scheduler.py` | passed | — |
| 2.8 CLI rollback + replay | `__main__.py`, `test_cli_rollback_replay.py` | 6 passed | `7982721` |
| 2.9 Tag v0.2.0 | — | — | tag pushed |

### Trạng thái repo:
- Branch: `main`
- Tag: `v0.2.0` (pushed)
- Full test suite: all passed

---

## Session Summary — 2026-05-14 (Phase 1 hoàn thành)

**Session này hoàn thành toàn bộ Phase 1 MVP Du lịch (task 1.9 → 1.17).**

### Tasks đã làm trong session này:

| Task | File chính | Tests | Commit |
|------|-----------|-------|--------|
| 1.9 Validator | `mapper/validator.py` | 14 passed | `7e1aba3` |
| 1.10 Dedup | `mapper/dedup.py` | 20 passed | `7bbee00` |
| 1.11 Backup | `filler/backup.py` | 10 passed | `01f4269` |
| 1.12 Excel filler | `filler/excel_filler.py` | 14 passed | `d87ed1d` |
| 1.13 Mail marker | `mail/marker.py` | 12 passed | `f479360` |
| 1.14 Logger | `utils/logger.py` | 9 passed | `eec1831` |
| 1.15 CLI entry | `__main__.py` (wired pipeline) | manual OK | `c2a0d1b` |
| 1.16 Smoke test | `tests/test_pipeline_smoke.py` | 9 passed | `e9700f2` |
| 1.17 Tag | `v0.1.0-mvp-dulich` | — | `e0ade3e` |

### Bugs phát hiện & fix trong session:
- **ruff SIM102**: nested `if` trong validator.py → merge thành 1 condition với `and`.
- **ruff UP038**: `isinstance(x, (int, float))` → `isinstance(x, int | float)`.
- **ruff SIM105**: `try/except/pass` → `contextlib.suppress(Exception)`.
- **ruff C901**: `_normalize_record` quá complex → dùng `contextlib.suppress` giảm branch count.
- **mypy attr-defined**: `ClassifierError`/`ValidationError` import từ `utils.errors`, không phải từ module gốc.
- **Dedup date bug**: pandas đọc date từ xlsx với `dtype=str` trả về `"2026-05-20 00:00:00"` → thêm format `"%Y-%m-%d %H:%M:%S"` vào `_parse_date`.
- **openpyxl date read-back**: openpyxl đọc `date` thành `datetime` → test dùng `.date()` để compare.

### Trạng thái repo:
- Branch: `main`
- Tag: `v0.1.0-mvp-dulich` (pushed)
- Full test suite: tất cả passed
- Pre-commit hooks (ruff + mypy + pytest): tất cả green

---

## Lịch sử (gần nhất ở trên)

### 2026-05-14 — Task 1.17 (Tag v0.1.0-mvp-dulich)
- **Task:** 1.17 Tag git v0.1.0-mvp-dulich
- **Trạng thái:** ✅ Done
- **Note:** Phase 1 MVP hoàn thành. Tag annotated tạo + push lên GitHub.

### 2026-05-14 — Task 1.16 (Smoke test)
- **Task:** 1.16 End-to-end smoke test
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `tests/test_pipeline_smoke.py` — 9 tests cover full pipeline (backup, classify, validate, dedup, fill, marker)
  - `src/auto_fill/mapper/dedup.py` — thêm format "%Y-%m-%d %H:%M:%S" vào _parse_date (fix pandas dtype=str)
- **Test:** `pytest tests/test_pipeline_smoke.py -v` → 9 passed. Full suite: all passed.
- **Note:** Phát hiện bug dedup: pandas đọc date từ xlsx về dạng "2026-05-20 00:00:00" khi dtype=str. Đã thêm format parsing.

### 2026-05-14 — Task 1.15 (CLI entry)
- **Task:** 1.15 CLI entry — `python -m auto_fill run --dry-run`
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/__main__.py` — cli group, run command (wired pipeline), rollback stub
- **Test:** `python -m auto_fill --help` OK. `python -m auto_fill run --help` OK. Full suite passed.
- **Note:** Pipeline wired: connect Outlook → backup → fetch → download → classify → read → normalize → validate → dedup → fill → mark. Dry-run: bỏ qua bước ghi/mark. Lỗi COM → sys.exit(1).

### 2026-05-14 — Task 1.14 (Logger)
- **Task:** 1.14 Logger — loguru JSON + stdlib intercept
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/utils/logger.py` — setup_logging(), _InterceptHandler
  - `tests/test_logger.py` — 9 unit tests
- **Test:** `pytest tests/test_logger.py -q` → 9 passed.
- **Note:** _InterceptHandler chuyển stdlib logging → loguru. setup_logging() gọi 1 lần tại CLI entry.

### 2026-05-14 — Task 1.13 (Mail marker)
- **Task:** 1.13 Mail marker — Mark Read + move to Processed folder
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/mail/marker.py` — mark_processed(), _get_or_create_folder()
  - `tests/test_marker.py` — 12 unit tests với MagicMock COM
- **Test:** `pytest tests/test_marker.py -q` → 12 passed.
- **Note:** Dùng olFolderInbox=6 để lấy Inbox. Tự tạo sub-folder "Processed" nếu chưa có. Lỗi COM → return False (không raise).

### 2026-05-14 — Task 1.12 (Excel filler)
- **Task:** 1.12 Excel filler — append rows vào sheet Du lịch
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/filler/excel_filler.py` — append_travel_rows(), _next_stt(), _write_row(), _coerce()
  - `tests/test_excel_filler.py` — 14 unit tests với openpyxl fixture
- **Test:** `pytest tests/test_excel_filler.py -q` → 14 passed. Full suite: all passed.
- **Note:** STT auto-increment (max+1). trip_days computed từ trip_end - trip_start. openpyxl đọc lại date thành datetime → test normalize với .date().

### 2026-05-14 — Task 1.11 (Backup)
- **Task:** 1.11 Backup snapshot master
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/filler/backup.py` — snapshot(), _purge_old()
  - `tests/test_backup.py` — 10 unit tests
- **Test:** `pytest tests/test_backup.py -q` → 10 passed.
- **Note:** Giữ tối đa 30 ngày backup, tự xóa folder cũ hơn. Tên folder = YYYY-MM-DD.

### 2026-05-14 — Task 1.10 (Dedup)
- **Task:** 1.10 Dedup lookup (CCCD, Ngày đi, Nơi đến)
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/mapper/dedup.py` — is_duplicate(), _load_sheet(), _rename_columns(), _check_match(), _parse_date()
  - `tests/test_dedup.py` — 20 unit tests với mock _load_sheet
- **Test:** `pytest tests/test_dedup.py -q` → 20 passed. Full suite: 184 passed.
- **Note:** Dedup so khớp case-insensitive destination, hỗ trợ nhiều format ngày (dd/mm/yyyy, yyyy-mm-dd, Excel serial). Load fail → False (safe default).

### 2026-05-14 — Task 1.9 (Validator)
- **Task:** 1.9 Validator required fields + type check
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/mapper/validator.py` — FieldSpec, ValidationResult, TRAVEL_SCHEMA, validate_record(), validate_and_raise()
  - `tests/test_validator.py` — 14 unit tests
- **Test:** `pytest tests/test_validator.py -q` → 14 passed.

### 2026-05-14 — Task 1.5 (Excel reader)
- **Task:** 1.5 Excel reader
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/reader/excel_reader.py` — read_excel(), _detect_header_row(), _build_rename_map(), _fuzzy_match()
  - `tests/test_excel_reader.py` — 12 unit tests, fixture tạo bằng openpyxl
- **Test:** `pytest tests/test_excel_reader.py -v` → 12 passed. Full suite: 42 passed.
- **Note:** Alias mapping dùng exact match + fuzzy (rapidfuzz ratio >= 85). Full aliases.yaml sẽ tạo ở task 2.3.

### 2026-05-14 — Task 1.4 (Attachment downloader)
- **Task:** 1.4 Attachment downloader
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/mail/downloader.py` — download_attachments(), _unique_path()
  - `tests/test_downloader.py` — 11 unit tests mock COM
- **Test:** `pytest tests/test_downloader.py -v` → 11 passed. Full suite: 30 passed.
- **Note:** Acceptance (chạy thực tế) cần Outlook chạy — user verify tay. Code đúng, mock tests cover các edge case chính.

### 2026-05-14 — Task 1.3 (Mail fetcher)
- **Task:** 1.3 Mail fetcher với mock COM unit test
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/mail/fetcher.py` — MailFetcher class: filter sender allowlist + subject regex
  - `tests/test_mail_fetcher.py` — 16 unit tests với MagicMock COM
  - `src/auto_fill/config/settings.py` — update default subject_pattern để match Vietnamese diacritics
  - `.env.example` — update SUBJECT_PATTERN tương ứng
- **Test:** `pytest tests/test_mail_fetcher.py -v` → 16 passed. Full suite: 19 passed.
- **Note:** Pattern gốc `c[aâ]p` không match "Cấp" (ấ ≠ a,â). Đã update thành `c[aâấ]p` để hỗ trợ tone marks.

### 2026-05-14 — Tasks 1.1, 1.2 (config + OutlookClient)
- **Task:** 1.1 Config layer, 1.2 OutlookClient
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `src/auto_fill/config/settings.py` — đã tồn tại từ prior session, verify OK
  - `src/auto_fill/mail/outlook_client.py` — mới tạo: OutlookClient + MailMessage dataclass + CLI
- **Test:** `pytest -v` → 3 passed. Import OK. Acceptance 1.1 (print settings path) OK với UTF-8 encoding.
- **Note:** Acceptance 1.2 (`python -m auto_fill.mail.outlook_client list`) cần Outlook Desktop đang chạy — user cần chạy tay để verify. Code đúng, import sạch.

### 2026-05-14 — Phase 0 complete (0.4–0.7)
- **Task:** 0.4, 0.5, 0.6, 0.7 (project config files + venv + pre-commit + git)
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `requirements.txt` — core + dev + docs deps
  - `pyproject.toml` — build, ruff, mypy, pytest config
  - `.gitignore` — exclude .env/data/logs/venv/xlsx
  - `.env.example` — template config với Outlook + paths
  - `README.md` — setup & usage guide
  - `.pre-commit-config.yaml` — ruff + mypy + pytest hooks
  - `.git/hooks/pre-commit` — installed via `pre-commit install`
- **Test:** `pytest -v` → 3 passed.
- **Note:** Tất cả files đã tồn tại từ session trước. Task 0.7 (git init + remote) đã được user hoàn thành. Chỉ chạy `pre-commit install` để kích hoạt hooks.

### 2026-05-14 — Phase 0 init
- **Task:** 0.1, 0.2, 0.3 (scaffold + docs + CLAUDE.md)
- **Trạng thái:** ✅ Done
- **File thay đổi:**
  - `CLAUDE.md`
  - `docs/ARCHITECTURE.md`
  - `docs/CODING_RULES.md`
  - `docs/DATABASE.md`
  - `docs/MAPPING.md`
  - `docs/TECH_STACK.md`
  - `docs/WORKFLOW.md`
  - `docs/TODO.md`
  - `docs/TASKS.md`
  - `docs/DECISIONS.md`
  - `docs/GLOSSARY.md`
  - `src/auto_fill/` (skeleton dirs)
- **Test:** N/A (docs only).
- **Note:** File tổng đã được scan: 20 sheets. Schema 6 sheet ưu tiên đã ghi vào DATABASE.md.

---

## Open Questions (cần user trả lời trước khi auto tiếp)

1. **Sender allowlist cho Outlook?**
   Cần list email của đại lý / nguồn gửi phiếu cấp đơn để filter mail.
   → Sẽ điền vào `.env` `SENDER_*`.

2. **Subject pattern chuẩn?**
   User có tiêu đề mail chuẩn không (vd `[Cấp đơn] Du lịch 14/05`)?
   Nếu không, dùng keyword match như MAPPING §5.

3. **File tổng path?**
   Hiện đang là `Danh sách cấp đơn Offline PTI  (3).xlsx`. Có cần đổi tên cho gọn?
   Đề xuất rename: `data/master/master.xlsx` (link symbolic / copy).

4. **Outlook profile?**
   Máy user dùng 1 profile Outlook hay nhiều? Folder Inbox nằm ở account nào?

5. **Backup giữ bao lâu?**
   Đề xuất: giữ 30 ngày trong `data/backup/`. Sau đó nén `.zip`.

6. **Schema cụ thể của 14 sheet còn lại?**
   MVP chỉ làm 6 sheet (Du lịch, Sức khỏe, Ô tô, Xe máy, BHYTBHXH, HSSV).
   14 sheet còn lại (TEMPLATE, Hủy, Hoàn phí, Nhà, ...) sẽ đào sâu ở Phase 2.

---

## Blocker hiện tại

(Không có)

---

## Format cho mỗi entry mới

Copy template này khi log task mới:

```
### YYYY-MM-DD HH:MM — <Task ID> <Tên task>
- **Trạng thái:** in_progress | done | blocked
- **File thay đổi:** `path/to/file1.py`, `path/to/file2.py`
- **Test:** `pytest tests/test_x.py` → pass/fail. Coverage X%.
- **Commit:** <hash> "<message>"
- **Note:** Ghi chú decision / vấn đề gặp phải.
- **Subtask phát sinh:** (nếu có, đã add vào TODO.md mục X.Y)
```
