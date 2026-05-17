# TODO.md — Master Task List

> Đây là **source of truth** cho auto-loop của Claude.
> Quy tắc: làm tuần tự từ trên xuống, tick `- [x]` sau khi xong và test pass.
> Subtask mới phát sinh → THÊM dưới task cha (không xen giữa task khác).

---

## Phase 0 — Project bootstrap

- [x] 0.1. Tạo cấu trúc thư mục `src/auto_fill/`, `tests/`, `data/`, `docs/`, `logs/`
- [x] 0.2. Viết toàn bộ docs/ (ARCHITECTURE, CODING_RULES, DATABASE, MAPPING, TECH_STACK, WORKFLOW, TODO, TASKS, DECISIONS, GLOSSARY)
- [x] 0.3. Viết `CLAUDE.md` ở root
- [x] 0.4. Tạo `requirements.txt`, `pyproject.toml`, `.gitignore`, `.env.example`, `README.md`
- [x] 0.5. Tạo virtualenv + cài dependencies (`pip install -r requirements.txt`)
- [x] 0.6. Cấu hình pre-commit (`ruff`, `mypy`, `pytest`)
- [x] 0.7. Git init + connect remote `https://github.com/VietAnh954/Project_Autofill_capDon.git` + first commit + first push (USER chạy tay 1 lần — xem GIT_WORKFLOW §8)
- [x] 0.8. Setup `.claude/settings.json` + slash commands `/next`, `/verify`, `/status`
- [x] 0.9. Setup `docs/GIT_WORKFLOW.md` để Claude tuân thủ commit/push policy

## Phase 1 — MVP (1 sản phẩm: Du lịch)

- [x] 1.1. **Config layer**: viết `src/auto_fill/config/settings.py` với pydantic-settings; load `.env`.
       Acceptance: `python -c "from auto_fill.config import settings; print(settings.master_file_path)"` chạy OK.
- [x] 1.2. **OutlookClient**: kết nối Outlook qua pywin32, list inbox.
       Acceptance: `python -m auto_fill.mail.outlook_client list` in ra 5 mail mới nhất.
- [x] 1.3. **Mail fetcher**: filter by sender allowlist + subject pattern, trả về iterator `MailMessage`.
       Acceptance: unit test mock COM, fetch trả đúng số mail match.
- [x] 1.4. **Attachment downloader**: save file vào `data/inbox/`.
       Acceptance: chạy thực tế trên 1 mail test → file xuất hiện trong inbox/.
- [x] 1.5. **Excel reader**: đọc file Excel attachment, detect header row, rename về canonical via alias.yaml.
       Acceptance: unit test với `tests/fixtures/sample_dulich.xlsx` → DataFrame có cột canonical.
- [x] 1.6. **CSV reader**: tương tự cho .csv.
- [x] 1.7. **Normalizer**: implement rules MAPPING §3 (date, CCCD, phone, money).
       Acceptance: unit test 10+ case mỗi rule.
- [x] 1.8. **Classifier**: implement MAPPING §5, chỉ support sheet "Du lịch" ở giai đoạn này.
- [x] 1.9. **Validator**: required fields, type check theo DATABASE §2.1.
- [x] 1.10. **Dedup**: lookup `(CCCD, Ngày đi, Nơi đến)` trong sheet Du lịch.
- [x] 1.11. **Backup**: snapshot master vào `data/backup/<date>/`.
- [x] 1.12. **Excel filler**: append rows vào sheet "Du lịch", STT auto, format date.
       Acceptance: chạy script tay với 3 record → file tổng có thêm đúng 3 dòng cuối sheet Du lịch.
- [x] 1.13. **Mail marker**: mark mail processed (Read + move folder).
- [x] 1.14. **Logger**: setup loguru JSON, log mỗi step.
- [x] 1.15. **CLI entry**: `python -m auto_fill run --dry-run` và `run`.
- [x] 1.16. **End-to-end smoke test**: 1 mail thật → 1 dòng mới trong master.
       Acceptance: pytest `tests/test_pipeline_smoke.py` xanh.
- [x] 1.17. Tag git `v0.1.0-mvp-dulich`.

## Phase 2 — Mở rộng sang 6 sheet chính

- [x] 2.1. Thêm classifier rule cho Sức khỏe, Ô tô, Xe máy, BHYTBHXH, HSSV.
- [x] 2.2. Viết mapping table cho từng sheet (đã có draft MAPPING §6).
- [x] 2.3. Viết `aliases.yaml` đầy đủ cho mọi canonical field.
- [x] 2.4. PDF reader (`pdf_reader.py`) với `pdfplumber`.
- [x] 2.5. PDF OCR fallback (`pytesseract`) cho phiếu scan.
- [x] 2.6. Report end-of-day: render `report_YYYY-MM-DD.md` + gửi qua Outlook.
- [x] 2.7. Scheduler: `apscheduler` poll mỗi 15 phút.
- [x] 2.8. CLI `rollback`, `replay`.
- [x] 2.9. Tag `v0.2.0`.

## Phase 3 — Database

- [x] 3.1. Thiết kế schema SQLite (DATABASE §5).
- [x] 3.2. `alembic init`, viết migration cho 6 sheet đầu.
- [x] 3.3. Script `tools/migrate_excel_to_sqlite.py` 1-shot.
- [x] 3.4. Refactor `filler/` → ghi DB trước, export Excel hàng ngày.
- [x] 3.5. CLI `export --sheet <name> --to <path>`.
- [x] 3.6. Tag `v0.3.0`.

## Phase 4 — Service / GUI / Cloud

- [x] 4.1. Đóng gói Windows service (NSSM).
- [x] 4.2. GUI Tkinter / PyQt cho non-tech user.
- [x] 4.3. Đẩy DB lên Postgres / cloud.
- [x] 4.4. API FastAPI cho query / export remote.

## Phase 5 — Documentation Website (GitHub Pages)

> Trang web mô tả project: cách làm, flow, hướng dẫn sử dụng, screenshot.
> Stack: MkDocs Material + GitHub Actions auto-deploy. Free, không cần server.
> Live URL (sau khi enable Pages): `https://vietanh954.github.io/Project_Autofill_capDon/`

- [x] 5.1. Cài thêm dev deps: `mkdocs-material`, `mkdocs-glightbox`, `mkdocs-mermaid2-plugin`.
       Acceptance: `mkdocs --version` chạy OK.
- [x] 5.2. Viết `mkdocs.yml` (config: theme, nav, plugin, markdown extensions).
- [x] 5.3. Tạo `site_docs/` chứa nội dung cho web (TÁCH biệt với `docs/` engineering).
       - `site_docs/index.md` — landing: vấn đề + giải pháp.
       - `site_docs/how-it-works.md` — sơ đồ flow (Mermaid).
       - `site_docs/installation.md` — hướng dẫn cài.
       - `site_docs/usage.md` — hướng dẫn dùng hằng ngày.
       - `site_docs/products.md` — list 20 sản phẩm BH hỗ trợ.
       - `site_docs/troubleshoot.md` — FAQ.
       - `site_docs/changelog.md` — auto-gen từ git tag.
- [x] 5.4. Test local: `mkdocs serve` → http://127.0.0.1:8000 hiển thị OK.
- [x] 5.5. Viết `.github/workflows/deploy-docs.yml` — build + push lên branch `gh-pages`.
       Acceptance: push lên main → Actions chạy xanh → site live.
- [x] 5.6. Enable GitHub Pages trong repo settings (USER chạy tay 1 lần).
- [x] 5.7. Thêm Custom domain (tuỳ chọn) nếu user có domain riêng. (skipped — không có custom domain)
- [x] 5.8. Tag `v0.5.0-docs-site`.

---

## Phase 6 — Web Dashboard + Gmail

### 6A — Web Dashboard (daily-use website, deployable)
- [x] 6.1. `pipeline_state.py`: trạng thái pipeline, logs deque, background subprocess runner.
- [x] 6.2. New API endpoints: `POST /pipeline/run`, `GET /pipeline/status`, `GET /pipeline/logs/stream` (SSE).
- [x] 6.3. FastAPI Jinja2Templates + StaticFiles setup.
- [x] 6.4. HTML templates: `base.html` (DaisyUI + Alpine.js CDN), `dashboard.html` (stats, pipeline control, log console), `records.html` (filter/search/paginate/export).
       Acceptance: `python -m auto_fill serve` → mở `http://localhost:8000/dashboard` hiển thị đúng.
- [x] 6.5. Tests: `pytest tests/test_dashboard_routes.py` xanh.

### 6B — Gmail source
- [x] 6.6. `mail/gmail_client.py`: OAuth2 + list messages (google-api-python-client).
- [x] 6.7. `mail/gmail_fetcher.py`: filter sender + subject → iterator `MailMessage`.
- [x] 6.8. `mail/gmail_downloader.py` + `mail/gmail_marker.py`: tải attachment, label "Processed".
- [x] 6.9. Tích hợp Gmail vào pipeline CLI flag `--source outlook|gmail|both`.
- [x] 6.10. Tests: `pytest tests/test_gmail_*.py` xanh.

### 6C — Wrap up
- [x] 6.11. Update `requirements.txt` + docs.
- [x] 6.12. Tag `v0.6.0`.

---

## Phase 7 — Mail Pattern Refinement (từ mẫu thực tế)

> Phát sinh sau khi user gửi `example_mail/mail1..mail4`. Xem `docs/MAIL_PATTERNS.md` cho 5 TYPE.
> Mục tiêu: pipeline đọc mail thực tế của Việt Anh / Affina mà không nhầm lẫn mail báo cáo / mail check phương án với mail cấp đơn.

- [x] 7.1. Tạo `src/auto_fill/mapper/skip_filter.py` — `classify_mail_type()` trả về A/B/C/D/E/review theo `MAIL_PATTERNS.md §6`.
       Acceptance: 4 mail mẫu trả đúng type (mail1=C, mail2=A, mail3=B, mail4=B).
- [x] 7.2. Tạo `src/auto_fill/mapper/email_quote.py` — strip nested reply quotes, chỉ lấy top-level body.
       Acceptance: unit test với mail3 (5 reply lồng) → body chỉ ~10 dòng đầu của Lien (TCGI).
- [x] 7.3. Tạo `src/auto_fill/reader/gcn_pdf_reader.py` — parse GCN từ TYPE B PDF.
       Extract: số GCN, BMBH, NĐBH, phí, thời hạn, sản phẩm.
       Acceptance: test với `GCN NGUYỄN ANH TÚ tái tục.pdf` → trả đủ 7 field.
- [x] 7.4. Update `mail/fetcher.py` để scan folder `Inbox\AutoFill\Incoming` thay vì `Inbox`.
       Backward-compat: nếu folder không tồn tại → fallback Inbox + log warning.
- [x] 7.5. Tạo `src/auto_fill/mail/folder_router.py` — sau process, move mail sang folder đúng:
       - TYPE A/B OK → `Processed/<today>/`
       - TYPE A/B fail validate → `Needs_Review/`
       - TYPE C/review → `Needs_Review/`
       - TYPE D → `Skipped/<today>/`
- [x] 7.6. Tạo `data/state/processed_mail_ids.txt` tracker + integrate vào fetcher (lớp 2 anti-double).
       Acceptance: chạy `run` 2 lần liên tiếp → lần 2 process 0 mail.
- [x] 7.7. CLI mới: `python -m auto_fill outlook setup-folders` — auto tạo 4 folder con của AutoFill.
- [x] 7.8. Update aliases.yaml với header thực từ Excel mail2 (Affina Care template):
       - `"tên người mua (*)"` → `buyer_name`
       - `"cmnd người mua (*)"` → `buyer_id_number`
       - `"họ tên người được bh (*)"` → `insured_name`
       - `"cccd người được bh (*)"` → `insured_id_number`
       - `"chương trình tham gia (*)"` → `plan`
       - `"số gcn/hđ cũ (*)"` → `previous_contract_number`
       - … (full list trong DATABASE.md §2.4)
- [x] 7.9. Reader Excel "Sức khỏe" — support 3-row header (row 1 = nhóm merged, row 2 = chi tiết, row 3 = ghi chú).
- [x] 7.10. Reader Excel — implement fill-down BMBH cho rows có cột BMBH trống nhưng cột NĐBH có data.
- [x] 7.11. Subject classifier — refine theo `MAIL_PATTERNS.md §4` (priority table 10–99).
- [x] 7.12. Test fixture từ 4 mail mẫu copy vào `tests/fixtures/example_mail/` (bỏ ảnh JPEG để giảm size).
- [x] 7.13. End-to-end test với 4 mail mẫu: 2 fill OK (mail2 + mail3 đối soát) + 1 review (mail1) + 1 đối soát (mail4).
- [x] 7.14. Update `site_docs/products.md` + `site_docs/how-it-works.md` với 5 TYPE mail và skip rules.
- [x] 7.15. Tag `v0.7.0-mail-refinement`.

---

## Phase 8 — Mapper Refactor (từ data thực tế file master PTI v5 + sample files)

> Phát sinh sau khi user upload `Danh sách cấp đơn Offline PTI (5).xlsx` + 5 sample file mẫu trong `sample_capdon/`.
> Mục tiêu: pipeline KHÔNG cứng nhắc bắt buộc đủ data; phân biệt rõ NĐBH vs BMBH; xử lý 3 patterns (self/1-1/1-N).
> Reference: `docs/DATABASE.md §2.2-§2.4`, `docs/MAPPING.md §1.1`.

- [x] 8.1. **Validator refactor** — `mapper/validator.py`:
       - ✅ Chỉ require **1 core field** per sheet (`insured_name` cho travel/health/bhyt/student, `insured_name` OR `plate_number` cho auto/motorbike).
       - ✅ Soft fields thiếu → log warning, KHÔNG raise `ValidationError`.
       - ✅ 24 unit tests pass + 193 tests overall green.
       - ✅ Verified 6 records từ sample_du_lich.xlsx đều pass (trước fix: 1 fail vì `issued_date`).

- [x] 8.2. **Normalizer + `_normalize_record` refactor** (was: Dual-DOB awareness — moved to 8.2b):
       - ✅ `normalize_id_number`: float CCCD `12345678901.0` → `'012345678901'` (strip `.0` + pad CCCD 11→12 digits).
       - ✅ `normalize_date`: thêm `yyyy/mm/dd`, `MM/dd/yyyy` (US fallback), `2026-05-15 00:00:00` (pandas Timestamp), `dd.mm.yyyy`.
       - ✅ `_is_nan_like()` helper: detect NaN/None/NaT/'nan'/'NaT'/'na'/'n/a'.
       - ✅ `_normalize_record` (in `__main__.py`): khi normalize fail HOẶC value là NaN → set field = None (thay vì để float lẫn lộn → validator báo sai type).
       - ✅ 81 unit tests pass (28 cases mới cho NaN + float CCCD + multi-format date).
       - ✅ End-to-end mock với row 6 sample_du_lich (NaN DOB + NaN ID + pandas Timestamp str trip_start) → validator PASS.

- [x] 8.2b. **Dual-DOB column awareness** — `mapper/sheet_mapping.py`:
       - ✅ Verify mapping `insured_dob` → đúng cột NĐBH (col 4 Sức khỏe, col 4 BHYTBHXH, col 3 HSSV).
       - ✅ Verify mapping `buyer_dob` → đúng cột BMBH (col 12 Sức khỏe, col 11 BHYTBHXH, col 13 HSSV).
       - ✅ Added missing buyer fields (buyer_relation/dob/id_number/phone/address/email) to HEALTH + STUDENT + BHYT_BHXH.
       - ✅ 2 acceptance tests: Pattern 1 (same DOB both cols), Pattern 2 (child_dob=2018-12-12 col4, mother_dob=1988-08-30 col12).
       - ✅ 49 sheet_mapping tests pass + 613 overall green.

- [x] 8.3. **Reverse-order mapper** — `mapper/header_detector.py`:
       - ✅ Detect cấu trúc: scan group header row cho "Bên mua bảo hiểm" / "Người được bảo hiểm" → order bmbh_first | insured_first | unknown.
       - ✅ `build_group_aware_col_map`: position-indexed rename (key=1-indexed col) → tránh duplicate key khi 2 cột "Ngày sinh" cùng header.
       - ✅ `excel_reader.py` tích hợp: nếu detect được group layout → dùng group-aware, else → standard alias.
       - ✅ Acceptance: sample_suc_khoe.xlsx (BMBH trái) → insured_dob=2018-12-12 (Phúc), buyer_dob=1988-08-30 (Thuận) KHÁC NHAU.
       - ✅ 18 tests pass + 631/631 overall.

- [x] 8.4. **Pattern 3 fill-down** — `reader/excel_reader.py`:
       - ✅ `_filldown_buyer` mở rộng: thêm `source_buyer_group_id` UUID — new UUID khi row có buyer data, fill-down UUID cùng group.
       - ✅ Fill-down đã có từ trước (ffill); task 8.4 thêm UUID tagging.
       - ✅ Acceptance: `sample_du_lich.xlsx` gia đình Phạm Minh Cường → 4 rows cùng UUID; Nguyễn Văn An UUID khác.
       - ✅ 23 excel_reader tests pass + 641/641 overall.

- [x] 8.5. **Self-buyer normalizer** — `mapper/self_buyer.py`:
       - ✅ `normalize_self_buyer(record)`: khi `buyer_relation == "Bản thân"` → fill-up insured→buyer hoặc buyer→insured, whichever side is empty.
       - ✅ Acceptance: 13 unit tests + sample_suc_khoe.xlsx case 1 (Bản thân) → buyer_name == insured_name = "Nguyễn Thị Tuyết Linh".
       - ✅ 650/650 overall tests pass.

- [x] 8.6. **Excel filler — preserve BMBH-empty for Pattern 3**:
       - ✅ `append_rows(records, col_map, master_path, sheet_name)` generic filler với `source_buyer_group_id` tracking.
       - ✅ `append_travel_rows` cũng hỗ trợ skip_buyer cho continuation rows.
       - ✅ 6 new tests cover Pattern 3 buyer-empty: first row full, continuation rows cols 11-17 empty.
       - ✅ 656/656 overall tests pass.

- [ ] 8.7. **Test fixtures** — copy `sample_capdon/` vào `tests/fixtures/sample_capdon/`:
       - End-to-end test cho cả 5 sheet.
       - Verify mỗi sample pass pipeline (read → classify → fill).

- [ ] 8.8. **Update `aliases.yaml`** — bổ sung alias chính xác từ data thực:
       - "Tên khách hàng" + group="Bên mua bảo hiểm" → `buyer_name`
       - "Họ tên" + group="Người được bảo hiểm" → `insured_name`
       - "Ngày sinh" + group context → `buyer_dob` HOẶC `insured_dob`
       - "Mối quan hệ" / "Quan hệ BMBH" → `buyer_relation`
       - "Bản thân" giá trị → flag `is_self_buyer`

- [ ] 8.9. **Dashboard enhancement** — show pattern indicator:
       - Recent records section: hiển thị icon Pattern 1/2/3 cho mỗi entry.
       - Filter theo BMBH (group view).

- [ ] 8.10. Tag `v0.8.0-mapper-refactor`.

---

## Backlog (chưa ưu tiên)

- [ ] Multi-tenant nếu mở rộng cho nhiều phòng ban.

---

## Auto-loop note (cho Claude)

Hết task chưa tick → in summary:
- Tổng task xong / total.
- Task kế tiếp.
- Open questions từ TASKS.md.
- Đề xuất commit / tag nếu vừa kết thúc 1 Phase.
