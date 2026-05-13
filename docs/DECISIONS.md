# DECISIONS.md — Architecture Decision Records (ADR)

> Mỗi quyết định kiến trúc lớn ghi 1 entry. Format gọn. Không xoá entry cũ.

---

## ADR-001: Dùng pywin32 COM thay vì IMAP / Microsoft Graph

**Date:** 2026-05-14
**Status:** Accepted
**Context:**
- User dùng Outlook Desktop trên Windows, không có quyền tạo app Azure / app password.
- Mail có thể nằm trong PST file local, không sync IMAP.
**Decision:** Dùng `pywin32` + COM `Outlook.Application`.
**Consequences:**
- ✅ Hoạt động offline, không cần network ra Microsoft.
- ✅ Truy cập được PST local.
- ❌ Chỉ chạy được trên Windows + máy có Outlook installed.
- ❌ Outlook phải đang mở (hoặc auto-start).
- 🔁 Nếu tương lai chuyển sang Microsoft 365 cloud → migrate sang Graph API.

---

## ADR-002: openpyxl thay vì xlwings

**Date:** 2026-05-14
**Status:** Accepted
**Context:** Cần ghi vào file Excel `.xlsx` mà GIỮ formula, format.
**Decision:** `openpyxl` ở chế độ `data_only=False`.
**Consequences:**
- ✅ Không cần Excel app chạy.
- ✅ Ghi vào file đang đóng.
- ❌ Một số formula phức tạp / chart có thể bị mất (đã test, chấp nhận được với file tổng hiện tại).
- ❌ Chậm hơn xlwings ở file rất lớn (> 50MB).

---

## ADR-003: Single-threaded ở MVP

**Date:** 2026-05-14
**Status:** Accepted
**Context:** File tổng có rủi ro race condition nếu nhiều process cùng ghi.
**Decision:** Single-threaded loop, lock file `.lock` bên cạnh master.
**Consequences:**
- ✅ Đơn giản, dễ debug.
- ✅ Đủ cho khối lượng hiện tại (< 100 mail/ngày).
- ❌ Khi cần scale → refactor sang queue (Redis / SQLite queue).

---

## ADR-004: Chưa dùng DB ngay từ đầu

**Date:** 2026-05-14
**Status:** Accepted (sẽ revisit ở Phase 3)
**Context:** User vẫn quen làm việc trực tiếp với Excel. DB cần thời gian học.
**Decision:** Phase 1-2 ghi thẳng vào Excel. Phase 3 thêm SQLite, Excel thành export view.
**Consequences:**
- ✅ User dùng được ngay từ tuần đầu.
- ✅ Tránh sai lệch dữ liệu giai đoạn đầu.
- ❌ Excel chậm dần khi data > 10k rows / sheet → cần migrate đúng hạn.
- ❌ Khó query phức tạp (lọc đa điều kiện).

---

## ADR-005: Vietnamese tên sheet, English tên code

**Date:** 2026-05-14
**Status:** Accepted
**Context:** User đặt tên sheet bằng tiếng Việt có dấu. Code thì cần ASCII.
**Decision:**
- Sheet name lưu nguyên (vd `"Du lịch"`).
- Code identifier dùng tiếng Anh snake_case (vd `travel_insurance`).
- Mapping 2 bên trong `src/auto_fill/config/sheet_registry.py`.
**Consequences:**
- ✅ User không cần đổi file tổng.
- ✅ Code clean, không có Unicode trong identifier.

---

## ADR-006: Append-only, không sửa dòng cũ

**Date:** 2026-05-14
**Status:** Accepted
**Context:** File tổng là production của user.
**Decision:** Pipeline CHỈ thêm dòng mới. Sửa / xoá phải qua tay user hoặc script riêng có log.
**Consequences:**
- ✅ An toàn data.
- ❌ Phiếu sửa đổi (sheet `SỬA ĐỔI`) cần xử lý khác — chấp nhận manual ở MVP.

---

## ADR-007: Canonical schema nội bộ bằng English snake_case

**Date:** 2026-05-14
**Status:** Accepted
**Context:** Header input mỗi đại lý 1 kiểu, không ổn định.
**Decision:** DataFrame nội bộ luôn dùng `insured_name`, `insured_dob`, ... bất kể input.
**Consequences:**
- ✅ Code dễ đọc, test ổn định.
- ✅ Đổi target sheet không phá reader.

---

## ADR-008: Auto-loop dựa trên TODO.md + TASKS.md

**Date:** 2026-05-14
**Status:** Accepted
**Context:** User muốn Claude tự chạy đến khi xong project.
**Decision:** Claude đọc CLAUDE.md → loop trên TODO.md, dừng khi gặp `OPEN QUESTIONS` / blocker.
**Consequences:**
- ✅ User chỉ cần review.
- ❌ Cần TODO.md được viết rất chi tiết (đã làm).
- ❌ Nếu blocker không rõ ràng → Claude có thể đoán sai → cần CODING_RULES + dedup rule chặt.

---

## Template cho ADR mới

```
## ADR-XXX: <Tiêu đề ngắn>

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-YYY
**Context:** (Vấn đề cần quyết định)
**Decision:** (Chọn cái gì)
**Consequences:**
- ✅ Lợi ích
- ❌ Bất lợi
- 🔁 Trade-off / khi nào revisit
```
