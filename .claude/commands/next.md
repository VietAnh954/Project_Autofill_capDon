---
description: Tiếp tục auto-loop — lấy task chưa tick đầu tiên trong docs/TODO.md, thực hiện theo CLAUDE.md §2, update TASKS.md, commit, lặp lại đến khi gặp blocker.
---

Thực hiện auto-loop:

1. Đọc `CLAUDE.md`, `docs/TODO.md`, `docs/TASKS.md`.
2. Tìm task `- [ ]` đầu tiên trong TODO.md.
3. Đọc các docs liên quan trước khi viết code (ARCHITECTURE, MAPPING, DATABASE, CODING_RULES).
4. Implement task, viết test, chạy `pytest -q`.
5. Update `docs/TASKS.md` với entry mới.
6. Tick `- [x]` task vừa xong trong `docs/TODO.md`.
7. `git add -A && git commit -m "<type>(<scope>): <task>"`.
8. Tiếp tục task kế tiếp.

Dừng khi:
- TODO.md hết task.
- Gặp blocker (xem CLAUDE.md §2).
- Test fail 2 lần liên tiếp.
- User gõ `stop`.

Sau mỗi lần dừng, in summary: task vừa xong, task kế tiếp, open questions.
