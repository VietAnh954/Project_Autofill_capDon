# TASKS.md — Active Task Log

> Nhật ký trạng thái task hiện tại + open questions.
> Claude update file này SAU KHI hoàn thành mỗi task trong TODO.md.

---

## Đang làm

Phase 8.1–8.9 ✅ done. Còn 8.10 (tag).

---

## Session Summary — 2026-05-18 (Phase 8.6–8.8: Filler, fixtures, aliases)

| Task | File chính | Tests | Trạng thái |
|------|-----------|-------|-----------|
| 8.6 Pattern 3 filler | `filler/excel_filler.py`, `tests/test_excel_filler.py` | +6 tests | ✅ |
| 8.7 Test fixtures | `tests/fixtures/sample_capdon/` (5 files), `tests/test_e2e_samples.py` | 21 e2e tests | ✅ |
| 8.8 aliases.yaml | `mapper/aliases.yaml` | 677 pass | ✅ |

**Aliases added (8.8):**
- `insured_name`: "tên người được bh", "ten nguoi duoc bh" (HSSV abbreviated header).
- `buyer_name`: "người yêu cầu bh", "nguoi yeu cau bh", "tên người yêu cầu bh", "ten nguoi yeu cau bh", "người yêu cầu bảo hiểm".
- `buyer_relation`: "mối quan hệ với nđbh", "moi quan he voi ndbh", "quan hệ với nđbh", "quan he voi ndbh", "mối quan hệ với người được bh".

**Note:** All 5 sample_capdon fixtures pass e2e pipeline (read → normalize → validate). Fuzzy threshold 85 too low for "ten nguoi duoc bh" vs "ten nguoi duoc bao hiem" → explicit aliases added.

**Next:** Phase 8.9 — dashboard pattern indicator.

---

## Session Summary — 2026-05-18 (Phase 8.5: Self-buyer normalizer)

| Task | File chính | Tests | Trạng thái |
|------|-----------|-------|-----------|
| 8.4 Pattern 3 UUID (fix commit) | `reader/excel_reader.py`, `mapper/aliases.yaml` | 23 passed | ✅ |
| 8.5 self_buyer | `mapper/self_buyer.py`, `tests/test_self_buyer.py` | 13 passed | ✅ |

**Full test suite: 650 passed**

### Chi tiết 8.4 commit fix:
- Pre-commit failed: aliases.yaml unstaged → "họ tên người mua" alias missing → buyer_name KeyError.
- Fix: staged aliases.yaml together with excel_reader.py + test_excel_reader.py.

### Chi tiết 8.5:
- `normalize_self_buyer(record)`: no-mutation dict, handles NaN/empty string/None as empty.
- Relations matched case-insensitively: "Bản thân", "ban than", "self", "chính mình".
- Bidirectional: buyer empty + insured present → copy to buyer; insured empty + buyer present → copy to insured.
- 13 unit tests + acceptance test against sample_suc_khoe.xlsx row 0 (Bản thân).

**Next:** 8.8 — Update aliases.yaml with accurate aliases from real data.

---

## Session Summary — 2026-05-18 (Phase 8.3: Reverse-order mapper)

**Trigger:** Auto-loop task 8.3.

**Root cause:** Pipeline dùng `{header_string: canonical}` rename map → khi 2 cột cùng tên "Ngày sinh" (BMBH + NDBH), dict key collision → cả 2 map về `insured_dob`. Column BMBH không có `buyer_dob`.

**Thiết kế:**
1. `_norm(s)`: strip accents + đổi đ→d trước khi regex → tránh lỗi Unicode với "Người được" (ờ, đ không phân rã qua NFD).
2. `detect_group_layout(raw_df)`: scan first 5 rows tìm "ben mua"/"nguoi duoc" → trả về `GroupLayout` với bmbh_cols + insured_cols (frozenset 1-indexed).
3. `build_group_aware_col_map(headers, aliases, layout)`: trả `{1-indexed_col: canonical}` (key = position, không phải header string) → không bị duplicate key.
4. `excel_reader.read_excel`: nếu group detected → dùng col_map, set `data_df.columns` trực tiếp.

**Files thay đổi:**
- `src/auto_fill/mapper/header_detector.py` — mới tạo: 110 lines.
- `src/auto_fill/reader/excel_reader.py` — tích hợp group-aware rename.
- `tests/test_header_detector.py` — 18 tests: detect_group_layout, build_group_aware_col_map, 5 acceptance tests với sample_suc_khoe.xlsx.

**Tests:** 18 new + 631/631 overall green.

**Kết quả sample_suc_khoe.xlsx:**
- Phúc (con): insured_dob=2018-12-12, buyer_dob=1988-08-30 (mẹ Thuận). KHÁC NHAU ✓
- Tuyết Linh (bản thân): insured_dob = buyer_dob = 1995-08-28. GIỐNG NHAU ✓

**Next:** Phase 8.4 — Pattern 3 fill-down (reader/excel_reader.py).

---

## Session Summary — 2026-05-18 (Phase 8.2b: Dual-DOB column awareness)

**Trigger:** Auto-loop task 8.2b.

**Root cause:** `sheet_mapping.py` HEALTH và STUDENT thiếu `buyer_dob` và các buyer fields còn lại.

| Sheet | insured_dob (trước) | buyer_dob (trước) | buyer_dob (sau) | buyer fields bổ sung |
|-------|:--:|:--:|:--:|------|
| Sức khỏe | col 4 ✓ | MISSING | col 12 ✅ | buyer_relation(11), buyer_id_number(13), buyer_phone(14), buyer_address(15), buyer_email(16) |
| BHYTBHXH | col 4 ✓ | col 11 ✓ | col 11 ✅ | buyer_address(14), buyer_phone(15), buyer_email(16) |
| HSSV | col 3 ✓ | MISSING | col 13 ✅ | buyer_id_number(14), buyer_email(15), buyer_phone(16), buyer_address(17) |

**Files thay đổi:**
- `src/auto_fill/mapper/sheet_mapping.py` — thêm buyer fields vào HEALTH, BHYT_BHXH, STUDENT.
- `tests/test_sheet_mapping.py` — thêm 20 tests: insured_dob col check, buyer_dob col check, dual-DOB distinct check, 2 acceptance tests (Pattern 1 self-buyer, Pattern 2 me-con).

**Tests:** 49 sheet_mapping tests pass + 613/613 overall green.

**Note:**
- Pattern 1 test: insured_dob = buyer_dob = 1995-08-28 -> ca col 4 va col 12 nhan cung value.
- Pattern 2 test: child_dob (2018-12-12) -> col 4, mother_dob (1988-08-30) -> col 12. KHAC NHAU.
- BHYT_BHXH da dung tu truoc (buyer_dob col 11). Chi bo sung 3 buyer fields con thieu.

**Next:** Phase 8.3 — Reverse-order mapper (header_detector.py).

---

## Session Summary — 2026-05-17 (Phase 8.2: Normalizer NaN + float CCCD + multi-format date)

**Trigger:** User test lần 2 với `sample_du_lich_2.xlsx`:
```
[skip] sample_du_lich_2.xlsx: Sai kieu truong 'insured_dob': can date, nhan float;
                              Sai kieu truong 'insured_id_number': can str, nhan float
```
5 rows OK, row 6 fail.

**Root cause chuỗi:**
1. Pandas đọc cell trống Excel → trả `NaN` (float).
2. `_normalize_record` check `is not None` — NaN ≠ None → check PASS.
3. Gọi `normalize_id_number(NaN)` / `normalize_date(NaN)` → raise `MappingError`.
4. `contextlib.suppress(Exception)` nuốt error → field giữ nguyên `NaN` (float).
5. Validator báo "can str, nhan float" / "can date, nhan float".

**Refactor:**

| Function | Trước | Sau |
|----------|-------|-----|
| `normalize_id_number` | `str(value).strip()` cho float → `"12345678901.0"` (sai) | Detect float → int → str (strip `.0`); pad CCCD 11→12 digits |
| `normalize_date` | 8 format | 14 format (thêm `yyyy/mm/dd`, `MM/dd/yyyy`, `dd.mm.yyyy`, `pandas Timestamp str`) |
| `_is_nan_like` | (chưa có) | Helper detect None/NaN/NaT/'nan'/'NaT'/'na'/'n/a' |
| `_normalize_record` | `with suppress(Exception)` → giữ nguyên giá trị fail | Check NaN trước; normalize fail → set field = None |

**Files thay đổi:**
- `src/auto_fill/mapper/normalizer.py` (314 lines, refactor toàn bộ + thêm 6 date format).
- `src/auto_fill/__main__.py` `_normalize_record()` — robust NaN-aware.
- `tests/test_normalizer.py` (+ 28 test cases mới: NaN, float CCCD, yyyy/mm/dd, MM/dd/yyyy, pandas Timestamp).

**Tests:**
- 81/81 unit tests pass (53 cũ + 28 mới).
- 193/193 integration tests pass.
- End-to-end mock row 6 (NaN DOB + NaN ID + pandas Timestamp str) → validator PASS ✓.

**Note:**
- `_normalize_record` không còn dùng `contextlib.suppress`. Lỗi normalize → set None thay vì swallow im lặng.
- Date format priority: VN `dd/mm/yyyy` ưu tiên TRƯỚC US `MM/dd/yyyy`. Ambiguous case như `05/01/2026` → 5 January (VN), không phải May 1 (US).

**Next:** Phase 8.2b — verify mapper write đúng cột (2 cột "Ngày sinh" trong master).

---

## Session Summary — 2026-05-17 (Phase 8.1: Validator linh hoạt)

**Trigger:** User test `python -m auto_fill run --dry-run` với `sample_du_lich.xlsx` → fail:
`Thieu truong bat buoc: 'issued_date'`

**Root cause:** `validator.py` cũ require 7 fields (issued_date, insured_name, insured_dob, insured_id_number, trip_start, trip_end, destination) — quá cứng nhắc với data thực tế từ sale.

**Refactor:**

| Trước | Sau |
|-------|-----|
| 7+ required fields per sheet | 1 CORE field per sheet (`insured_name`, hoặc `OR plate_number` cho auto/motorbike) |
| Thiếu field → raise `ValidationError`, skip row | Thiếu soft field → log warning, vẫn ghi cell trống |
| Chỉ schema `travel` | Schema cho 6 sheet MVP: travel, health, auto, motorbike, bhyt_bhxh, student |

**Files thay đổi:**
- `src/auto_fill/mapper/validator.py` (239 lines, refactor hoàn chỉnh).
- `tests/test_validator.py` (154 lines, 24 tests cover CORE/SOFT logic + sub-classes per schema).

**Tests:**
- 24/24 unit test pass.
- 193/193 integration test (validator + smoke + pipeline + classifier + normalizer + dedup + readers) pass.
- Mock 6 records từ `sample_du_lich.xlsx` → 6/6 PASS (warnings = 3-10 soft fields trống nhưng vẫn ghi được).

**Note kỹ thuật:**
- Write tool có bug truncate file khi nội dung có nhiều Unicode/quote phức tạp → đã workaround bằng cách viết qua bash + python heredoc.
- `expected_type` của FieldSpec đổi từ `type | None` → `Any` để chấp nhận tuple `(int, float)` cho premium fields.

**Next:** Phase 8.2 — dual-DOB awareness (đảm bảo `insured_dob` ≠ `buyer_dob` khi ghi vào master).

---

## Session Summary — 2026-05-16 (Phase 7: Mail Pattern Refinement)

| Task | File chính | Tests | Trạng thái |
|------|-----------|-------|-----------|
| 7.1 skip_filter | `mapper/skip_filter.py` | 22 passed | ✅ |
| 7.2 email_quote | `mapper/email_quote.py` | 14 passed | ✅ |
| 7.3 gcn_pdf_reader | `reader/gcn_pdf_reader.py` | 16 passed | ✅ |
| 7.4 fetcher + outlook folder | `mail/fetcher.py`, `outlook_client.py` | 20 passed | ✅ |
| 7.5 folder_router | `mail/folder_router.py`, `outlook_client.py` | 14 passed | ✅ |
| 7.6 processed_tracker | `mail/processed_tracker.py`, `mail/fetcher.py` | 10 passed | ✅ |
| 7.7 outlook setup-folders CLI | `__main__.py`, `outlook_client.py` | CLI verified | ✅ |
| 7.8 aliases.yaml Affina Care | `mapper/aliases.yaml` | 53 fields, loads OK | ✅ |
| 7.9 3-row header + normalize | `reader/excel_reader.py` | 532 passed | ✅ |

**Full test suite: 532 passed**

### Chi tiết 7.9:
- Added `header_row: int | None = None` param to `read_excel()` for explicit override
- Added `_normalize_header(raw: str)` — collapses newlines/tabs to single space
- Added `_DATA_ROW_NUMERIC_RATIO = 0.20` constant (lowered from 0.30)
- Rewrote `_detect_header_row()`: numeric-cell ratio >20% → data row; header block = contiguous non-data rows from row 0; returns last row of block
- Verified: Affina Care mail2 Excel (3-row merged header) auto-detects row 2 as header → canonical columns OK

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
