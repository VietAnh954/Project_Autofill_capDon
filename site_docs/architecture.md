# Kiến trúc

> Tóm tắt từ [docs/ARCHITECTURE.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/ARCHITECTURE.md). Đọc bản đầy đủ trong repo.

## :material-cube-outline: Package layout

```
src/auto_fill/
├── config/     # pydantic-settings, sheet registry
├── mail/       # Outlook COM client + fetcher + attachment
├── reader/     # Excel/CSV/PDF readers
├── mapper/     # Classifier + normalizer + field map
├── filler/     # Excel writer + dedup + validator
├── storage/    # Backup + logger + (future) DB
└── utils/      # paths, date utils, errors
```

!!! info "Nguyên tắc"
    Mỗi module chỉ phụ thuộc module bên TRÁI nó trong pipeline.
    Reader không biết Outlook. Filler không gọi Reader trực tiếp.

## :material-chart-timeline-variant: Tech stack

| Layer | Library | Lý do |
|-------|---------|-------|
| Mail | `pywin32` (COM) | Native Windows, không cần API |
| Excel | `openpyxl` | Giữ formula, không cần Excel app |
| Data | `pandas` | Tiêu chuẩn ngành |
| Config | `pydantic-settings` | Type-safe, đọc `.env` |
| Logging | `loguru` | JSON format dễ dàng |
| Retry | `tenacity` | Decorator cho COM/network |
| Fuzzy | `rapidfuzz` | Match header cột |
| CLI | `click` | Quen thuộc |
| Test | `pytest` | Tiêu chuẩn |
| Lint | `ruff` + `mypy` | Nhanh, all-in-one |

Chi tiết: [docs/TECH_STACK.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/TECH_STACK.md).

## :material-file-document-multiple-outline: 11 docs nội bộ

| File | Mục đích |
|------|----------|
| [CLAUDE.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/CLAUDE.md) | Auto-loop instruction cho Claude Code |
| [ARCHITECTURE.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/ARCHITECTURE.md) | Pipeline, module boundary |
| [CODING_RULES.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/CODING_RULES.md) | Python standard |
| [DATABASE.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/DATABASE.md) | Schema file Excel tổng + roadmap DB |
| [MAPPING.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/MAPPING.md) | Canonical schema + alias + per-sheet mapping |
| [TECH_STACK.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/TECH_STACK.md) | Library + lý do |
| [WORKFLOW.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/WORKFLOW.md) | Sequence diagram |
| [GIT_WORKFLOW.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/GIT_WORKFLOW.md) | Commit/push policy |
| [DECISIONS.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/DECISIONS.md) | ADR — 8 quyết định kiến trúc |
| [GLOSSARY.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/GLOSSARY.md) | Viết tắt BH (NĐBH, BMBH, TNDS…) |
| [TODO.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/TODO.md) | Master task list cho auto-loop |
| [TASKS.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/TASKS.md) | Trạng thái + open questions |
| [SETUP_VSCODE.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/SETUP_VSCODE.md) | Setup VSCode + Claude Code |

## :material-shield-check: ADRs (Architecture Decision Records)

1. Dùng pywin32 COM thay vì IMAP/Graph
2. openpyxl thay vì xlwings
3. Single-threaded ở MVP
4. Chưa dùng DB ngay từ đầu
5. Tên sheet tiếng Việt giữ nguyên, code English
6. Append-only, không sửa dòng cũ
7. Canonical schema nội bộ bằng English snake_case
8. Auto-loop dựa trên TODO.md + TASKS.md

Đọc lý do từng quyết định: [DECISIONS.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/DECISIONS.md).
