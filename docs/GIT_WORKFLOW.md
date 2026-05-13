# GIT_WORKFLOW.md — Quy tắc Git/GitHub

> Áp dụng cho **solo project**. Đơn giản, không có team review.
> Claude PHẢI tuân thủ. Mỗi task xong → commit + push. KHÔNG để commit treo cục bộ.

---

## 1. Repo

- **Local:** `C:\Users\ADMIN\OneDrive\Company\Project_Autofill_capDon`
- **Remote:** `https://github.com/VietAnh954/Project_Autofill_capDon.git`
- **Default branch:** `main`

---

## 2. Branch strategy (solo)

| Branch | Mục đích | Push policy |
|--------|----------|-------------|
| `main` | Branch chính, mọi commit task đẩy thẳng vào. | Push sau mỗi task. |
| `feat/<phase>-<task>` (tuỳ chọn) | Khi task lớn / rủi ro (DB migration, refactor). | PR vào main, squash merge. |

Mặc định: **commit thẳng `main` cho mọi task trong TODO.md** (single dev, nhanh gọn).
Chỉ branch riêng khi:
- Task sửa schema lớn (Phase 3 DB migration).
- Refactor chạm > 5 file core.
- Experiment / spike.

---

## 3. Commit message (Conventional Commits)

Format bắt buộc:

```
<type>(<scope>): <subject ngắn, < 72 ký tự, imperative>

<body — optional, mô tả tại sao chứ không phải làm gì>

Refs: TODO #<task-id>
```

### Type

| Type | Khi nào dùng |
|------|--------------|
| `feat` | Thêm chức năng mới (cho TODO task implement) |
| `fix` | Sửa bug |
| `refactor` | Đổi cấu trúc code, không đổi behavior |
| `docs` | Sửa file `docs/`, `README`, comment |
| `test` | Thêm/sửa test |
| `chore` | Build, deps, config |
| `perf` | Tối ưu performance |
| `style` | Format, lint fix |

### Scope (theo module)

`mail` · `reader` · `mapper` · `filler` · `storage` · `config` · `cli` · `docs` · `tests` · `repo` · `ci` · `site`

### Ví dụ tốt

```
feat(mail): fetch unread mails matching subject pattern

Outlook COM connect via pywin32. Filter by sender allowlist + regex.
Returns iterator of MailMessage dataclass.

Refs: TODO #1.2
```

```
fix(reader): handle header row detection for sheet "Sức khỏe"

Sheet này có header ở row 3 chứ không phải row 1 như default.
Added _detect_header_row() heuristic.

Refs: TASKS open question Q3
```

```
docs(mapping): add alias for "ho ten ndbh" → insured_name

Refs: TODO #2.3
```

### Ví dụ XẤU (Claude tuyệt đối KHÔNG dùng)

- ❌ `update`
- ❌ `wip`
- ❌ `fix bug`
- ❌ `asdf`
- ❌ `Update file CLAUDE.md` (không có type/scope, không thông tin)

---

## 4. Auto-loop git steps (Claude thực hiện sau mỗi task)

```bash
# Sau khi code + test pass:
git status                              # Verify clean state
git add -A                              # Stage all
git diff --cached --stat                # Review what's staged
git commit -m "<type>(<scope>): <msg>" -m "Refs: TODO #X.Y"
git push origin main                    # Bắt buộc — KHÔNG để commit treo local
```

Nếu push fail (network / auth):
1. Log warning.
2. Retry 1 lần sau 10s.
3. Vẫn fail → DỪNG auto-loop, báo user "push failed: <reason>".

---

## 5. Tag policy

Tag khi:
- Kết thúc 1 Phase trong TODO.md.
- Trước khi merge branch lớn.
- Release minor (`v0.X.0`) / patch (`v0.X.Y`).

```bash
git tag -a v0.1.0-mvp-dulich -m "Phase 1 MVP: pipeline Du lịch end-to-end"
git push origin v0.1.0-mvp-dulich
```

Roadmap tags (sync với TODO.md):

| Tag | Trigger |
|-----|---------|
| `v0.0.1-bootstrap` | Hết Phase 0 |
| `v0.1.0-mvp-dulich` | Hết Phase 1 |
| `v0.2.0-multi-product` | Hết Phase 2 |
| `v0.3.0-database` | Hết Phase 3 |
| `v0.4.0-service` | Hết Phase 4 |
| `v0.5.0-docs-site` | Hết Phase 5 (website docs live) |
| `v1.0.0` | Production ready |

---

## 6. KHÔNG được commit

Đã list trong `.gitignore`, nhưng nhắc lại:
- `.env` (credential, sender list)
- `data/` (file thật của khách hàng — riêng tư)
- `logs/`
- `*.xlsx` (trừ fixture trong `tests/fixtures/`)
- `.venv/`
- `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`

Nếu nhỡ stage → **abort commit ngay**, `git restore --staged <file>`.

---

## 7. Khi conflict (hiếm xảy ra vì solo)

```bash
git pull --rebase origin main
# Xử lý conflict thủ công
git add <resolved-files>
git rebase --continue
git push origin main
```

Nếu Claude gặp conflict → DỪNG auto-loop, báo user.

---

## 8. First-time setup (user chạy 1 lần trên Windows)

```powershell
cd C:\Users\ADMIN\OneDrive\Company\Project_Autofill_capDon

# Nếu có folder .git cũ bị lỗi (kiểm tra: nếu git status báo lỗi)
# Bật View → Hidden files trong File Explorer rồi xoá .git folder thủ công
# HOẶC: Remove-Item -Recurse -Force .git

# Init
git init
git branch -M main
git config user.name "VietAnh954"
git config user.email "nguyenvietanh92tn@gmail.com"

# Connect remote
git remote add origin https://github.com/VietAnh954/Project_Autofill_capDon.git

# Auth — chọn 1 trong 2:
# Cách A (khuyến nghị): Git Credential Manager — chỉ cần đăng nhập 1 lần, dùng OAuth.
#   Đảm bảo đã cài Git for Windows mới nhất (có GCM kèm theo).
#   Khi push lần đầu, browser popup → đăng nhập GitHub bằng tài khoản VietAnh954.
# Cách B: Personal Access Token (PAT)
#   github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
#   → Generate new → scope: repo (đủ) → copy token.
#   Khi git push hỏi password → paste token.

# First commit + push
git add -A
git status                               # Verify chỉ source code, không có .env/data
git commit -m "chore(repo): bootstrap project structure and docs

- CLAUDE.md auto-loop instructions
- docs/ (ARCHITECTURE, CODING_RULES, DATABASE, MAPPING, TECH_STACK,
  WORKFLOW, TODO, TASKS, DECISIONS, GLOSSARY, GIT_WORKFLOW, SETUP_VSCODE)
- src/auto_fill/ skeleton
- pyproject.toml, requirements.txt, .pre-commit-config.yaml
- .vscode/, .claude/

Refs: TODO #0.1 #0.2 #0.3 #0.4 #0.7"

git push -u origin main
```

Sau bước này, mọi commit Claude làm tiếp theo CHỈ cần `git push origin main` (auto-loop tự xử).

---

## 9. Enable GitHub Pages (cho Phase 5 docs site)

Sau khi push lần đầu:

1. Vào https://github.com/VietAnh954/Project_Autofill_capDon → Settings → Pages.
2. Source: **GitHub Actions**.
3. Save.

Khi Phase 5 hoàn thành, mỗi push lên `main` sẽ tự build MkDocs + deploy tới:
`https://vietanh954.github.io/Project_Autofill_capDon/`

Quyền cần thiết cho Actions:
- Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save.

---

## 10. Recovery / rollback

```powershell
# Xem 10 commit gần nhất
git log --oneline -10

# Revert 1 commit cụ thể (an toàn, tạo commit mới đảo)
git revert <hash>
git push origin main

# Hoặc force về commit cũ (NGUY HIỂM — chỉ khi chắc chắn)
git reset --hard <hash>
git push --force-with-lease origin main
# Sau force, update lại docs/TASKS.md + docs/TODO.md cho khớp
```

Note: `.claude/settings.json` đã **deny `git push --force`** mặc định. Khi cần force, user phải tự gõ tay trong terminal.
