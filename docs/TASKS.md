# TASKS.md — Active Task Log

> Nhật ký trạng thái task hiện tại + open questions.
> Claude update file này SAU KHI hoàn thành mỗi task trong TODO.md.

---

## Đang làm

(Task 1.14 in_progress — Logger)

---

## Lịch sử (gần nhất ở trên)

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
