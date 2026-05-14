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
- [ ] 4.4. API FastAPI cho query / export remote.

## Phase 5 — Documentation Website (GitHub Pages)

> Trang web mô tả project: cách làm, flow, hướng dẫn sử dụng, screenshot.
> Stack: MkDocs Material + GitHub Actions auto-deploy. Free, không cần server.
> Live URL (sau khi enable Pages): `https://vietanh954.github.io/Project_Autofill_capDon/`

- [ ] 5.1. Cài thêm dev deps: `mkdocs-material`, `mkdocs-glightbox`, `mkdocs-mermaid2-plugin`.
       Acceptance: `mkdocs --version` chạy OK.
- [ ] 5.2. Viết `mkdocs.yml` (config: theme, nav, plugin, markdown extensions).
- [ ] 5.3. Tạo `site_docs/` chứa nội dung cho web (TÁCH biệt với `docs/` engineering).
       - `site_docs/index.md` — landing: vấn đề + giải pháp.
       - `site_docs/how-it-works.md` — sơ đồ flow (Mermaid).
       - `site_docs/installation.md` — hướng dẫn cài.
       - `site_docs/usage.md` — hướng dẫn dùng hằng ngày.
       - `site_docs/products.md` — list 20 sản phẩm BH hỗ trợ.
       - `site_docs/troubleshoot.md` — FAQ.
       - `site_docs/changelog.md` — auto-gen từ git tag.
- [ ] 5.4. Test local: `mkdocs serve` → http://127.0.0.1:8000 hiển thị OK.
- [ ] 5.5. Viết `.github/workflows/deploy-docs.yml` — build + push lên branch `gh-pages`.
       Acceptance: push lên main → Actions chạy xanh → site live.
- [ ] 5.6. Enable GitHub Pages trong repo settings (USER chạy tay 1 lần).
- [ ] 5.7. Thêm Custom domain (tuỳ chọn) nếu user có domain riêng.
- [ ] 5.8. Tag `v0.5.0-docs-site`.

---

## Backlog (chưa ưu tiên)

- [ ] Hỗ trợ Gmail (Phase 5).
- [ ] Multi-tenant nếu mở rộng cho nhiều phòng ban.
- [ ] Web dashboard hiển thị status realtime.

---

## Auto-loop note (cho Claude)

Hết task chưa tick → in summary:
- Tổng task xong / total.
- Task kế tiếp.
- Open questions từ TASKS.md.
- Đề xuất commit / tag nếu vừa kết thúc 1 Phase.
