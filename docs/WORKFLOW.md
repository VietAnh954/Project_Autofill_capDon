# WORKFLOW.md

> Flow chạy end-to-end khi pipeline được trigger (manual hoặc scheduled).

---

## 1. Trigger

3 cách trigger:
1. **Manual CLI**: `python -m auto_fill run` (MVP).
2. **VSCode task**: nhấn `F1 → Run Task → Auto-fill: run once`.
3. **Scheduled** (Phase 2): `apscheduler` chạy mỗi 15 phút.

---

## 2. Sequence diagram

```
User              CLI            OutlookClient     Reader     Mapper      Filler         Logger
 │                 │                  │              │           │           │              │
 │─── run ───────>│                  │              │           │           │              │
 │                │── connect() ───>│              │           │           │              │
 │                │                  │── fetch ──>(mail list)  │           │              │
 │                │<── mails ────────│              │           │           │              │
 │                │                                                                          │
 │                │ for each mail:                                                           │
 │                │   ├── save attachment ──> data/inbox/                                    │
 │                │   ├── read ──────────────> DataFrame                                    │
 │                │   ├── classify ─────────────────> sheet_name                           │
 │                │   ├── normalize ────────────────> canonical records                    │
 │                │   ├── validate ────────────────> ok / fail list                        │
 │                │   ├── dedup ────────────────────> new records                          │
 │                │   ├── backup master ──> data/backup/<date>/                              │
 │                │   ├── append rows ──> master file                                        │
 │                │   ├── log ─────────────────────────────────────────────> logs/app.jsonl │
 │                │   └── mark mail processed (move in Outlook)                              │
 │                │                                                                          │
 │                │── summary ──> stdout + email report (Phase 2)                           │
 │<── done ───────│                                                                          │
```

---

## 3. Step-by-step (chi tiết logic)

### Step 1: Connect Outlook
- `OutlookClient` dùng `win32com.client.Dispatch("Outlook.Application")`.
- Lấy namespace `MAPI`, mở Inbox (folder ID config trong `.env`).
- Validate Outlook đang chạy; nếu chưa → start Outlook hoặc fail-fast (config quyết định).

### Step 2: Fetch mails
- Lọc: `Unread = True` AND `SenderEmailAddress IN allowlist` AND `Subject MATCH pattern`.
- Allowlist + pattern config ở `.env`.
- Trả về iterator `MailMessage` (dataclass: `id, subject, sender, received_at, attachments[]`).

### Step 3: Save attachments
- Mỗi attachment → `data/inbox/<msg_id>_<original_filename>`.
- Skip file > MAX_SIZE (config, default 20MB).
- Skip extension không hỗ trợ (chỉ chấp nhận `.xlsx, .xls, .csv, .pdf`).

### Step 4: Read
- Detect file type bằng extension + magic bytes.
- Gọi `excel_reader`, `csv_reader`, hoặc `pdf_reader`.
- Reader trả `pd.DataFrame` cột canonical (đã rename theo MAPPING §4).
- KHÔNG validate value ở đây — chỉ structure.

### Step 5: Classify (chọn sheet)
- Theo PRIORITY (MAPPING §5):
  1. Sender allowlist match.
  2. Subject keyword match.
  3. Column signature.
  4. Fallback → unclassified.
- Output: `sheet_name` (str) hoặc `None`.

### Step 6: Normalize
- Apply rules MAPPING §3 cho từng cột canonical.
- Output: list `dict` đã chuẩn hoá.

### Step 7: Validate
- Kiểm required field (xem DATABASE per-sheet).
- Kiểm type, format (date hợp lệ, premium > 0, CCCD đúng độ dài).
- Record fail → đẩy `data/failed/invalid/`, KHÔNG ghi.

### Step 8: Dedup
- Lookup key (DATABASE §4) trong sheet đích.
- Trùng → đẩy `data/failed/duplicates/`, log warning.
- Chưa trùng → giữ.

### Step 9: Backup master
- Copy `master.xlsx` → `data/backup/YYYY-MM-DD/master_<HH-MM-SS>.xlsx`.
- Chỉ backup 1 lần / ngày trừ khi config `BACKUP_EVERY_RUN=true`.

### Step 10: Append
- Load master, append rows vào sheet đích (max_row+1).
- STT auto. Date → cell format `dd/mm/yyyy`.
- Lưu vào path mới: `data/processed/YYYY-MM-DD/master.xlsx`.
- Sau khi save thành công → **atomic rename** đè lên master gốc.

### Step 11: Mark processed
- Trong Outlook: mark mail là Read + move sang folder `Processed/<date>`.
- Move attachment file từ `data/inbox/` → `data/processed/<date>/`.

### Step 12: Log + Report
- 1 log JSON / mail.
- Cuối run: in summary stdout (X mails, Y rows, Z failed).
- Phase 2: tạo `report_YYYY-MM-DD.md` + gửi mail lại cho user.

---

## 4. Edge cases (xử lý sẵn)

| Case | Hành vi |
|------|---------|
| Mail không có attachment | Skip, log info. |
| Attachment encrypted/password | Skip, đẩy fail/encrypted/, log warning. |
| Master file đang mở (Excel lock) | Retry 3 lần (10s), fail → báo user. |
| Network drop giữa chừng | Tenacity retry. Mail chưa mark Read → lần sau chạy lại được. |
| 2 mails cùng phiếu (forward) | Dedup ở Step 8 sẽ catch. |
| Sheet đích không tồn tại trong master | Fail-fast, báo user (KHÔNG tự tạo sheet). |
| Header row khác kỳ vọng | Reader có `_detect_header_row()`; fail → fail/. |
| Thay đổi schema file tổng | Validation ở Step 10 phát hiện cột mismatch → dừng auto-loop, báo blocker. |

---

## 5. Idempotency

- Cùng 1 mail chạy 2 lần → KHÔNG ghi 2 lần (dedup + mark processed).
- An toàn để Cron / Scheduler retry.

---

## 6. Rollback

- Bug ghi sai vào master? Restore từ `data/backup/<date>/`.
- Có script `tools/rollback.py --to <backup_file>` (sẽ tạo ở Phase 1 task 5).

---

## 7. Performance budget (MVP)

| Step | Target |
|------|--------|
| Fetch 50 mails | < 30s |
| Read 1 attachment Excel 1MB | < 2s |
| Append 100 rows vào master 6MB | < 5s |
| End-to-end 50 mails (mỗi 10 rows) | < 5 phút |

Vượt → optimize (load `read_only=True` chỗ read, batch append, ...).
