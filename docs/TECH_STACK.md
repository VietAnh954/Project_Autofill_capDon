# TECH_STACK.md

> Danh sách công nghệ/library dùng trong dự án, lý do chọn và alternatives.

---

## 1. Runtime

| Item | Choice | Version | Lý do |
|------|--------|---------|-------|
| Language | Python | 3.11+ | Sẵn lib cho Excel/Outlook; `tomllib`, typing tốt. |
| OS target | Windows 10/11 | — | Outlook desktop chỉ chạy Windows (COM). |
| Package manager | pip + venv | — | Đơn giản. Sau có thể đổi `uv`. |

---

## 2. Core libraries

| Library | Mục đích | Lý do chọn | Alternative |
|---------|----------|-----------|-------------|
| `pywin32` | Outlook COM (đọc mail, tải attachment) | Native, không cần API key, hoạt động offline. | `exchangelib` (IMAP/EWS), Microsoft Graph |
| `openpyxl` | Đọc/ghi `.xlsx` | Giữ formula, formatting, không cần Excel chạy. | `xlwings` (cần Excel), `pandas.to_excel` |
| `pandas` | Manipulate dataframe | Tiêu chuẩn ngành. | `polars` (Phase 2 nếu cần perf) |
| `pydantic` + `pydantic-settings` | Config + validation | Type-safe, đọc `.env` chuẩn. | `dynaconf`, custom |
| `python-dotenv` | Load `.env` | Tích hợp sẵn với pydantic-settings. | — |
| `loguru` | Logging | Đơn giản hơn `logging` builtin; format JSON dễ. | stdlib `logging` |
| `tenacity` | Retry | Decorator gọn cho retry COM/network. | manual |
| `rapidfuzz` | Fuzzy match header → canonical | Nhanh hơn `fuzzywuzzy`. | `difflib` |
| `click` | CLI | Quen thuộc, dễ extension. | `typer`, `argparse` |
| `pytest` | Test | Tiêu chuẩn. | `unittest` |
| `ruff` | Linter + formatter | Nhanh, all-in-one (thay black+flake8+isort). | `black`+`flake8`+`isort` |
| `mypy` | Type check | Bắt lỗi sớm. | `pyright` |
| `pre-commit` | Git hook | Đảm bảo CODING_RULES tự động enforce. | husky-like |

---

## 3. Phase 2 additions

| Library | Mục đích |
|---------|----------|
| `pdfplumber` / `pypdf` | Đọc PDF phiếu cấp đơn |
| `pytesseract` + Tesseract OCR | OCR PDF scan |
| `jinja2` | Template báo cáo HTML |
| `apscheduler` | Lập lịch chạy tự động (poll mail mỗi 15') |

---

## 4. Phase 3 additions

| Library | Mục đích |
|---------|----------|
| `sqlalchemy` + `alembic` | ORM + migration |
| `sqlite3` (stdlib) | DB local trước, dễ chuyển Postgres |
| `psycopg2-binary` | Khi đẩy lên Postgres |
| `fastapi` (nếu cần API) | Expose query/export endpoint |

---

## 5. Không dùng (đã cân nhắc)

| Library | Lý do loại |
|---------|-----------|
| `xlsxwriter` | Chỉ ghi được, không đọc → không thay được openpyxl. |
| `xlwings` | Cần Excel app chạy → khó automation server. |
| `O365` (Microsoft Graph SDK) | Cần đăng ký app Azure, phức tạp ở MVP. User dùng Outlook desktop. |
| `selenium` | Không cần browser automation. |
| `airflow` / `prefect` | Quá nặng cho MVP single-user. |

---

## 6. Cài đặt nhanh (sẽ ở README.md)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
pre-commit install
```

---

## 7. requirements.txt (sẽ tạo ở Phase 0)

```
# core
pywin32>=306
openpyxl>=3.1
pandas>=2.1
pydantic>=2.5
pydantic-settings>=2.1
python-dotenv>=1.0
loguru>=0.7
tenacity>=8.2
rapidfuzz>=3.5
click>=8.1

# dev
pytest>=7.4
pytest-cov>=4.1
ruff>=0.1
mypy>=1.7
pre-commit>=3.5
```
