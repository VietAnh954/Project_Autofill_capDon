---
description: Verify trạng thái dự án — chạy test, ruff, mypy, kiểm tra TODO/TASKS đồng bộ.
---

Verify checklist:

1. `pytest -q` → phải xanh.
2. `ruff check src tests` → 0 issue.
3. `mypy src` → 0 error.
4. Đếm task `- [ ]` còn lại trong `docs/TODO.md`.
5. Kiểm tra `docs/TASKS.md`: task `in_progress` cuối có khớp với HEAD commit không.
6. Kiểm tra `git status` clean (không có file pending).

In summary dạng table:

| Check | Result |
|-------|--------|
| pytest | ✅/❌ |
| ruff | ✅/❌ |
| mypy | ✅/❌ |
| Task pending | N |
| Git clean | ✅/❌ |
