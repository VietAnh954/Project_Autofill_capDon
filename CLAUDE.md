# CLAUDE.md — Master Instructions for Auto-Fill Cấp Đơn

> File này được Claude (trong VSCode / Claude Code) đọc TỰ ĐỘNG mỗi phiên làm việc.
> KHÔNG xoá. KHÔNG sửa nếu chưa hiểu mục đích.

---

## 1. Mục tiêu dự án (read first, every session)

Tự động hoá việc nhập liệu "phiếu cấp đơn bảo hiểm" từ email vào file Excel tổng
(`Danh sách cấp đơn Offline PTI.xlsx`) — thay cho việc copy-paste tay hằng ngày.

Pipeline: **Email Outlook → Tải attachment → Đọc file (Excel/CSV/PDF) → Mapping
field → Phân loại sản phẩm bảo hiểm → Ghi vào sheet tương ứng trong file tổng →
Backup + log → (tương lai) đẩy DB**.

---

## 2. Quy tắc làm việc tự động (AUTO-LOOP)

Khi user gõ `go`, `continue`, `/next`, hoặc bất kỳ lệnh nào ngụ ý "tiếp tục",
Claude PHẢI thực hiện theo đúng vòng lặp dưới đây:

```
LOOP:
  1. Read docs/TODO.md → tìm task chưa check `- [ ]` đầu tiên.
  2. Read docs/TASKS.md → kiểm tra trạng thái task hiện tại (in_progress?).
  3. Read các docs liên quan (ARCHITECTURE, MAPPING, CODING_RULES...) trước khi code.
  4. Thực hiện task:
       - Viết code tối thiểu cần thiết.
       - Tuân thủ CODING_RULES.md.
       - Nếu chạm DB schema → đọc DATABASE.md trước.
       - Nếu chạm mapping field → đọc MAPPING.md trước.
  5. Chạy test / smoke check (xem TASKS.md mục Acceptance).
  6. Update docs/TASKS.md: log kết quả, vấn đề gặp phải, file đã đổi.
  7. Tick `- [x]` task vừa xong trong docs/TODO.md.
  8. Nếu phát sinh subtask mới → THÊM vào TODO.md (KHÔNG tự ý làm ngay,
     trừ khi cần để task hiện tại pass).
  9. Commit git với message: `feat(<scope>): <task summary>` (xem CODING_RULES).
  10. Quay lại bước 1 cho tới khi TODO.md hết task chưa tick HOẶC gặp blocker.
```

**Blocker = dừng auto-loop khi:**
- Cần credential / secret mà chưa có trong `.env`.
- Schema file tổng thay đổi mà MAPPING.md chưa cập nhật.
- Test fail không tự sửa được sau 2 lần thử.
- Ambiguity về business logic — ghi câu hỏi vào `docs/TASKS.md` mục **OPEN QUESTIONS**, rồi dừng.

---

## 3. Thứ tự đọc docs (priority)

Mỗi lần bắt đầu một task mới, đọc theo thứ tự:

1. `CLAUDE.md` (file này)
2. `docs/TODO.md` — biết task nào kế tiếp
3. `docs/TASKS.md` — biết context hiện tại + open questions
4. `docs/ARCHITECTURE.md` — chỉ khi task chạm cấu trúc
5. `docs/MAPPING.md` — bắt buộc khi task liên quan đọc/ghi field
6. `docs/DATABASE.md` — bắt buộc khi task chạm file tổng / DB
7. `docs/CODING_RULES.md` — bắt buộc trước khi viết bất kỳ file Python nào
8. `docs/TECH_STACK.md` — khi cần biết dùng lib nào
9. `docs/WORKFLOW.md` — khi cần hiểu flow end-to-end
10. `docs/DECISIONS.md` — khi muốn hiểu "tại sao chọn cách này"
11. `docs/GLOSSARY.md` — khi gặp từ viết tắt / domain term không rõ

---

## 4. Quy ước giao tiếp với user

- **Trả lời ngắn gọn**. Đừng giải thích lại những gì user vừa đọc trong docs.
- Khi xong 1 task: liệt kê (a) file thay đổi, (b) lệnh test đã chạy, (c) task kế tiếp.
- Khi không chắc: hỏi 1 câu duy nhất, KHÔNG đoán bừa rồi sửa lại.
- Tiếng Việt cho mọi log/message hướng user. Tiếng Anh cho code, commit, identifier.

---

## 5. Cảnh báo (hard rules — KHÔNG được phá)

| Rule | Tại sao |
|------|---------|
| KHÔNG ghi đè file tổng gốc. Luôn copy ra `data/processed/` rồi sửa. | Tránh mất dữ liệu sản xuất. |
| KHÔNG xoá hàng/sheet trong file tổng, dù trông như rỗng. | Có thể là formula / template ẩn. |
| KHÔNG hardcode credential. Dùng `.env` + `src/auto_fill/config/`. | Bảo mật. |
| KHÔNG commit file `data/`, `logs/`, `.env`, `*.xlsx` thật. | Tránh leak data khách hàng. |
| KHÔNG đổi schema file tổng không hỏi user. | Đây là production file của user. |
| Trước mọi ghi đè → backup vào `data/backup/YYYY-MM-DD/`. | Rollback an toàn. |

---

## 6. Stop conditions (khi nào dừng auto-loop)

Auto-loop DỪNG (và báo user) khi:
- Hết task trong TODO.md.
- Gặp blocker (xem mục 2).
- Test fail 2 lần liên tiếp trên cùng task.
- User gõ `stop`, `pause`, `halt`.
- Phát hiện thay đổi schema file tổng so với DATABASE.md.

---

## 7. Khi user mở project lần đầu trong VSCode

Claude tự động:
1. Đọc CLAUDE.md (file này).
2. Đọc `docs/TODO.md` và `docs/TASKS.md`.
3. Báo user: "Sẵn sàng. Task kế tiếp: `<task>`. Gõ `go` để bắt đầu."
4. KHÔNG tự chạy task nào trước khi user xác nhận lần đầu.
