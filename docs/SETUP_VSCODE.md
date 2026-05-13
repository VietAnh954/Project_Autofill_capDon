# SETUP_VSCODE.md — Set up Claude + VSCode để auto chạy project

> Đọc 1 lần khi bắt đầu. Sau đó mọi thứ tự động qua `CLAUDE.md` + `docs/TODO.md`.

---

## 1. Cài đặt một lần (15 phút)

### 1.1. VSCode

Tải tại https://code.visualstudio.com/ → cài bình thường.

### 1.2. Extension Claude Code

Mở VSCode → tab Extensions (`Ctrl+Shift+X`) → tìm **"Claude Code"** (publisher: Anthropic) → Install.

(VSCode sẽ tự gợi ý cài luôn các extension khác đã liệt kê trong `.vscode/extensions.json`:
Python, Pylance, Ruff, Mypy, GitLens. Bấm "Install All".)

### 1.3. Python 3.11+

Tải Python 3.11 hoặc 3.12 tại https://www.python.org/downloads/ — nhớ tick "Add to PATH" lúc cài.

Verify:
```powershell
python --version
# Python 3.11.x hoặc 3.12.x
```

### 1.4. Git

Tải tại https://git-scm.com/download/win.

### 1.5. (Tuỳ chọn) Anthropic CLI

Nếu muốn dùng Claude từ terminal ngoài VSCode:
```powershell
# Cài Claude Code CLI (tham khảo docs.claude.com để có link mới nhất)
npm i -g @anthropic-ai/claude-code
```

---

## 2. Mở project trong VSCode

```powershell
cd C:\Users\ADMIN\OneDrive\Company\Project_Autofill_capDon
code .
```

VSCode sẽ:
- Tự đọc `.vscode/settings.json` (đã set Python interpreter, Ruff, pytest).
- Hiện popup "Recommended extensions" → cài hết.
- Claude Code extension tự đọc `CLAUDE.md` ở root.

---

## 3. Khởi tạo môi trường Python (1 lần)

Mở Terminal trong VSCode (`Ctrl+`` `):

```powershell
# 1. Tạo venv
python -m venv .venv

# 2. Kích hoạt (PowerShell)
.venv\Scripts\Activate.ps1

# Nếu PowerShell chặn execution policy:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Cài deps
pip install -r requirements.txt
pip install -e .

# 4. Cài pre-commit hook
pre-commit install

# 5. Test
pytest -q
# Tất cả phải pass (smoke test).
```

---

## 4. Cấu hình `.env` (1 lần)

```powershell
copy .env.example .env
notepad .env
```

Điền tối thiểu:
- `MASTER_FILE_PATH` — đường dẫn tới file Excel tổng (copy file `Danh sách cấp đơn Offline PTI (3).xlsx` vào `data/master/master.xlsx`).
- `SENDER_ALLOWLIST` — email các đại lý / nguồn gửi phiếu.
- `OUTLOOK_PROFILE` — tên profile Outlook (xem trong Control Panel → Mail).

---

## 5. Khởi động auto-mode với Claude

### 5.1. Lần đầu (orientation)

1. Trong VSCode, mở Claude Code panel (icon Claude bên thanh hoạt động, hoặc `Ctrl+Shift+P` → "Claude: Open").
2. Claude tự đọc `CLAUDE.md` ở root. CLAUDE.md có 2 dòng `@docs/TODO.md` và `@docs/TASKS.md` → Claude Code tự pull 2 file đó vào context.
3. Claude báo task kế tiếp: ví dụ "Task tiếp theo: 0.4 — Tạo requirements.txt..."

### 5.2. Auto chạy

Gõ vào chat Claude:
```
go
```
hoặc
```
/next
```

Claude sẽ:
1. Lấy task `- [ ]` đầu tiên trong `docs/TODO.md`.
2. Đọc docs liên quan trước khi viết code.
3. Viết code + test.
4. Chạy `pytest -q`.
5. Update `docs/TASKS.md`.
6. Tick `- [x]` task vừa xong.
7. `git add -A && git commit -m "..."`.
8. Lặp đến task kế tiếp.

### 5.3. Slash commands có sẵn

| Lệnh | Hành vi |
|------|---------|
| `/next` | Tiếp tục auto-loop (lấy task tiếp). |
| `/status` | In trạng thái project (không thực hiện task). |
| `/verify` | Chạy pytest + ruff + mypy + check git clean. |

### 5.4. Khi nào Claude dừng

Auto-loop DỪNG khi:
- Hết task trong TODO.md.
- Gặp `OPEN QUESTIONS` trong `docs/TASKS.md`.
- Test fail 2 lần liên tiếp.
- User gõ `stop` / `pause`.
- Phát hiện schema file tổng đổi so với `docs/DATABASE.md`.

Khi dừng, Claude in summary và đợi user.

---

## 6. Workflow hằng ngày

### Buổi sáng

1. Mở VSCode → folder project tự load.
2. `git pull` (nếu sync nhiều máy).
3. `.venv\Scripts\Activate.ps1`.
4. Trong chat Claude: gõ `/status` xem hôm qua đến đâu.
5. Gõ `go` → Claude tiếp tục.

### Khi review code Claude viết

- VSCode hiện diff (GitLens).
- Đọc commit message + files thay đổi.
- Nếu OK → để Claude chạy tiếp.
- Nếu sai → gõ `stop`, sửa tay, rồi `go` lại.

### Khi muốn rollback 1 task

```powershell
git log --oneline | Select-Object -First 10
git revert <commit-hash>
```

Sau đó update lại `docs/TODO.md` (tick về `- [ ]`) và `docs/TASKS.md`.

---

## 7. Tips tối ưu token (rất quan trọng cho cost)

### 7.1. Mục tiêu

Mỗi lần chat, Claude tự load `CLAUDE.md` + `docs/TODO.md` + `docs/TASKS.md`.
3 file này phải gọn — KHÔNG bloat.

### 7.2. Quy tắc giữ token thấp

| Quy tắc | Lý do |
|---------|-------|
| Mỗi doc < 500 dòng | Giảm context init. |
| `docs/TASKS.md` chỉ giữ 5 entry gần nhất, archive cũ sang `docs/archive/TASKS_<month>.md` | Hạn chế lịch sử dài. |
| TODO.md tick xong → vẫn giữ (cho audit), nhưng nhóm "Completed phase" có thể fold | Phase cũ ít cần đọc. |
| Mã code → đặt trong `src/`, KHÔNG inline vào docs | Claude chỉ Read khi cần. |
| Long output (full file dump) → không paste vào chat, để Claude tự Read | Tránh duplicate. |
| Khi xong 1 Phase → tạo `docs/PHASES/PHASE_X_SUMMARY.md` ngắn 30 dòng | Replace nhiều file dài bằng 1 file ngắn. |
| Dùng `/status` thay vì hỏi free-text | Slash command đi thẳng tới logic, ngắn hơn. |

### 7.3. Anti-pattern (đốt token)

- ❌ Paste cả output `pytest -v` (vài ngàn dòng) vào chat. → để Claude tự chạy + đọc.
- ❌ Hỏi "tóm tắt lại toàn bộ project" mỗi lần. → đọc `/status` đã đủ.
- ❌ Yêu cầu Claude generate code rồi vứt đi. → Plan trước, code sau.
- ❌ Mở 10 file đính kèm vào chat khi chỉ cần 1.

### 7.4. Khi nào nên reset session

- Khi context window > 70%: bảo Claude `summarize this session vào docs/TASKS.md`, sau đó mở chat mới.
- Cuối ngày: luôn reset session mới.

---

## 8. Backup & safety

| Item | Cách backup |
|------|-------------|
| Code | Git (commit từng task). Push lên private repo (GitHub / GitLab) tuần / lần. |
| File tổng `master.xlsx` | Pipeline tự backup vào `data/backup/<date>/`. Cron Windows nén `data/backup/` qua tuần. |
| `.env` | KHÔNG commit. Backup tay vào password manager (1Password / Bitwarden). |
| DB (Phase 3) | `sqlite3 .backup` daily, đẩy lên OneDrive. |

---

## 9. Khi cần đổi máy

```powershell
# Máy mới
git clone <repo-url> auto-fill-capdon
cd auto-fill-capdon
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
copy .env.example .env
# Sửa .env với path mới
pre-commit install
pytest -q
```

---

## 10. Troubleshoot

| Triệu chứng | Cách xử |
|-------------|--------|
| `pywin32` không import được | `python -m pywin32_postinstall -install` (admin) |
| Outlook COM lỗi `RPC_E_DISCONNECTED` | Outlook chưa mở. Mở Outlook trước, hoặc set `OUTLOOK_AUTO_START=true` |
| `pre-commit` chậm | Lần đầu cài hooks, lần sau nhanh. |
| Ruff/mypy fail trong VSCode nhưng pass CLI | Reload Window: `Ctrl+Shift+P` → "Reload Window". |
| Claude không đọc CLAUDE.md | Check `.claude/settings.json` mục `context.alwaysIncludeFiles`. |
| Test fail "module not found" | Đảm bảo `pip install -e .` đã chạy. |
| File tổng mở trong Excel → ghi fail | Đóng Excel trước khi chạy pipeline (hoặc dùng cơ chế lock đã build). |
