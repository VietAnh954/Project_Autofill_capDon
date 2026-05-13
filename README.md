# auto-fill-capdon

> Tự động hoá nhập liệu phiếu cấp đơn bảo hiểm từ Outlook vào file Excel tổng.

## Mục đích

Thay cho việc copy-paste tay phiếu cấp đơn từ email vào file Excel tổng mỗi ngày,
pipeline này tự động:

1. Đọc mail mới từ Outlook Desktop.
2. Tải attachment (Excel/CSV/PDF).
3. Phân loại sản phẩm bảo hiểm.
4. Chuẩn hoá dữ liệu.
5. Ghi vào sheet đúng trong file tổng (append-only, có dedup).
6. Backup + log + report.

## Cấu trúc dự án

```
.
├── CLAUDE.md              # Instruction cho Claude (auto-loop)
├── README.md              # File này
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CODING_RULES.md
│   ├── DATABASE.md
│   ├── DECISIONS.md
│   ├── GLOSSARY.md
│   ├── MAPPING.md
│   ├── TASKS.md
│   ├── TECH_STACK.md
│   ├── TODO.md
│   └── WORKFLOW.md
├── src/
│   └── auto_fill/
│       ├── config/
│       ├── mail/
│       ├── reader/
│       ├── mapper/
│       ├── filler/
│       ├── storage/
│       └── utils/
├── tests/
├── data/
│   ├── master/            # Symlink hoặc copy của file tổng
│   ├── inbox/
│   ├── processed/
│   ├── failed/
│   └── backup/
└── logs/
```

## Setup nhanh

```powershell
# 1. Clone về máy (hoặc mở folder hiện tại trong VSCode)
cd C:\Users\ADMIN\OneDrive\Company\Project_Autofill_capDon

# 2. Tạo venv
python -m venv .venv
.venv\Scripts\activate

# 3. Cài dependencies
pip install -r requirements.txt
pip install -e .

# 4. Cấu hình
copy .env.example .env
# Mở .env và điền: sender allowlist, đường dẫn file tổng, Outlook folder

# 5. Hook
pre-commit install

# 6. Chạy thử
python -m auto_fill run --dry-run
```

## Chạy

```powershell
# Dry-run (đọc nhưng không ghi)
python -m auto_fill run --dry-run

# Chạy thật
python -m auto_fill run

# Rollback từ backup
python -m auto_fill rollback --to data/backup/2026-05-14/master_09-30-00.xlsx
```

## Phát triển với Claude (auto-mode)

Mở folder này trong VSCode có **Claude Code** extension cài sẵn.

1. Claude tự đọc `CLAUDE.md` ngay khi mở folder.
2. Claude báo task kế tiếp từ `docs/TODO.md`.
3. Gõ `go` (hoặc `/next`) → Claude tự thực hiện task → update `docs/TASKS.md` → commit → chuyển task tiếp.
4. Gõ `stop` để dừng.

Xem chi tiết quy tắc auto-loop ở `CLAUDE.md` mục 2.

## Bảo mật

- KHÔNG commit `.env`, `data/`, `logs/`, file `.xlsx` thật.
- Credential Outlook là native (không cần lưu password).
- Log che 4 ký tự cuối CCCD/CMND.

## License

Internal. Không public.
