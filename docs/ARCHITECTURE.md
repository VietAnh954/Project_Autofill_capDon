# ARCHITECTURE.md

> Mục đích: Mô tả kiến trúc tổng thể của `auto-fill-capdon`.
> Khi Claude thực hiện bất kỳ task động chạm structure → đọc file này TRƯỚC.

---

## 1. High-level pipeline

```
┌──────────────┐    ┌──────────┐    ┌─────────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│  Outlook     │ →  │  Mail    │ →  │   Reader    │ →  │ Mapper │ →  │ Filler │ →  │Storage │
│  Desktop     │    │ (fetch)  │    │ (xlsx/csv/  │    │(classify│    │(append  │    │(backup │
│  (.pst/COM)  │    │attachment│    │  pdf parse) │    │+normalize│   │+dedup)  │    │+log +DB│
└──────────────┘    └──────────┘    └─────────────┘    └────────┘    └────────┘    └────────┘
                                                                          │
                                                                          ▼
                                                                  Master Excel
                                                            "Danh sách cấp đơn..."
```

---

## 2. Module boundaries (Python package layout)

```
src/auto_fill/
├── config/         # Pydantic settings, load .env
│   └── settings.py
├── mail/           # Đọc Outlook desktop qua pywin32 COM
│   ├── outlook_client.py   # Kết nối Outlook
│   ├── fetcher.py          # Lấy mail mới, lọc subject/sender
│   └── attachment.py       # Tải attachment về data/inbox/
├── reader/         # Đọc nội dung attachment
│   ├── excel_reader.py     # openpyxl + pandas
│   ├── csv_reader.py
│   └── pdf_reader.py       # (Phase 2)
├── mapper/         # Chuẩn hoá + phân loại sản phẩm
│   ├── classifier.py       # Đoán sheet đích (Du lịch / Ô tô / ...)
│   ├── normalizer.py       # Chuẩn hoá ngày, CCCD, số điện thoại
│   └── field_map.py        # Mapping từ field input → cột target
├── filler/         # Ghi vào file tổng
│   ├── excel_writer.py     # openpyxl, append-only
│   ├── dedup.py            # Check trùng theo CCCD + số HĐ
│   └── validator.py        # Validate trước khi ghi
├── storage/        # Backup + log + (future) DB
│   ├── backup.py
│   ├── logger.py
│   └── db.py               # (Phase 3) SQLite/Postgres
└── utils/
    ├── paths.py
    └── date_utils.py
tests/
data/
  ├── inbox/        # Mail attachment vừa tải
  ├── processed/    # Đã xử lý OK
  ├── failed/       # Lỗi → cần review tay
  └── backup/       # Snapshot file tổng theo ngày
logs/
docs/
```

**Nguyên tắc:** mỗi module chỉ phụ thuộc module bên TRÁI nó trong pipeline.
Reader không biết Outlook tồn tại. Filler không gọi Reader trực tiếp.

---

## 3. Data flow chi tiết

### 3.1. Mail → Inbox
- Outlook COM lọc mail có subject match pattern (cấu hình ở `.env`,
  ví dụ: `"phiếu cấp đơn"`, `"BH xe máy"`, ...).
- Mỗi mail xử lý xong → đánh dấu đã đọc + move sang folder `Processed` trong Outlook.
- Attachment tải về `data/inbox/<msg_id>_<filename>`.

### 3.2. Reader → DataFrame chuẩn
- Mỗi file đầu vào → trả về `pandas.DataFrame` với **cột chuẩn nội bộ**
  (xem `docs/MAPPING.md` mục "Internal canonical fields").
- Reader KHÔNG quyết định sheet đích. Chỉ trích xuất + parse.

### 3.3. Mapper → tagged record
- `classifier.py` đoán `sheet_name` dựa trên:
  - Tên file / sheet input (`"du_lich"`, `"oto"`, ...).
  - Từ khoá trong subject email.
  - Cột đặc trưng (có cột "Biển số" → ô tô / xe máy).
- Output: `{"sheet": "Du lịch", "records": [dict, dict, ...]}`.

### 3.4. Filler → ghi file tổng
- Mở file tổng ở chế độ `data_only=False` để giữ formula.
- Append vào sheet đích, ở dòng `max_row + 1`.
- Đánh STT tự động.
- Dedup bằng key `(CCCD, Số HĐ)`. Trùng → đẩy sang `data/failed/`.
- Lưu file đã sửa vào `data/processed/<date>/<file>.xlsx`.
- Backup nguyên trạng vào `data/backup/<date>/` TRƯỚC khi sửa.

### 3.5. Logger / Report
- Log JSON dòng (`logs/app.jsonl`) — 1 record / 1 mail xử lý.
- Cuối ngày: sinh report `report_<YYYY-MM-DD>.md` gửi lại user qua email (Phase 2).

---

## 4. Concurrency & state

- **Single-threaded** ở MVP. Tránh race khi nhiều process cùng mở file tổng.
- File tổng được "lock" bằng cách tạo `.lock` file cùng thư mục.
  Process khác thấy `.lock` → đợi hoặc fail-fast.

---

## 5. Error handling strategy

| Tầng | Lỗi điển hình | Cách xử lý |
|------|---------------|------------|
| Mail | Outlook chưa mở, network | retry x3, sau đó log + skip. |
| Reader | File hỏng, sheet không tồn tại | move vào `data/failed/` + log. |
| Mapper | Không classify được sheet | đẩy `failed/unclassified/`, log + báo. |
| Filler | Validate fail | KHÔNG ghi, đẩy `failed/invalid/`, log chi tiết field nào sai. |
| Storage | Disk full, permission | crash hard, alert user. |

---

## 6. Roadmap phase (đồng bộ với TODO.md)

| Phase | Mô tả | Trạng thái |
|-------|-------|-----------|
| 0 | Setup repo, docs, skeleton | ⏳ |
| 1 | MVP: 1 sheet (Du lịch), Outlook → Excel | ⏳ |
| 2 | Toàn bộ 20 sheets + PDF reader + report email | ⏳ |
| 3 | DB SQLite, query/export ngược | ⏳ |
| 4 | Tách service / scheduler / GUI | ⏳ |

---

## 7. Trade-offs đã chọn (link tới DECISIONS.md)

- ADR-001: Vì sao dùng **pywin32 COM** thay vì IMAP / Microsoft Graph.
- ADR-002: Vì sao **openpyxl** thay vì xlwings.
- ADR-003: Vì sao xử lý **single-threaded** ở MVP.
- ADR-004: Vì sao chưa dùng DB ngay từ đầu.
