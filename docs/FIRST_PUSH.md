# FIRST_PUSH.md — Hướng dẫn đẩy code lần đầu lên GitHub

> Làm 1 LẦN DUY NHẤT. Sau đó Claude tự `git commit + push` sau mỗi task.

Repo target: **https://github.com/VietAnh954/Project_Autofill_capDon**

---

## :material-numeric-0-circle-outline: Trước khi bắt đầu — checklist

- [ ] Đã cài **Git for Windows** ([tải tại đây](https://git-scm.com/download/win)). Verify: `git --version` chạy được.
- [ ] Đã có tài khoản GitHub `VietAnh954`.
- [ ] Repo `Project_Autofill_capDon` đã được tạo trên GitHub (empty — không init README/license, không gì cả).
- [ ] Đang ở folder dự án trong PowerShell:
  ```powershell
  cd C:\Users\ADMIN\OneDrive\Company\Project_Autofill_capDon
  ```

---

## :material-numeric-1-circle: Dọn folder `.git` cũ (nếu có)

Sandbox của Claude trước đó có thể đã tạo dở folder `.git`. Phải xoá trước khi init fresh.

```powershell
# Kiểm tra
Test-Path .git
# Nếu trả True → xoá:
Remove-Item -Recurse -Force .git
```

Nếu báo "Access denied" → mở **File Explorer** → bật **View → Show → Hidden items** → vào folder `.git` → xoá tay.

---

## :material-numeric-2-circle: Init git + cấu hình identity

```powershell
git init
git branch -M main
git config user.name "VietAnh954"
git config user.email "nguyenvietanh92tn@gmail.com"
```

Verify:
```powershell
git config --list | Select-String "user."
```
Phải thấy `user.name=VietAnh954` và `user.email=nguyenvietanh92tn@gmail.com`.

---

## :material-numeric-3-circle: Kết nối remote GitHub

```powershell
git remote add origin https://github.com/VietAnh954/Project_Autofill_capDon.git
git remote -v
```
Output mong đợi:
```
origin  https://github.com/VietAnh954/Project_Autofill_capDon.git (fetch)
origin  https://github.com/VietAnh954/Project_Autofill_capDon.git (push)
```

---

## :material-numeric-4-circle: Verify `.gitignore` đang hoạt động (QUAN TRỌNG)

```powershell
git status
```

**KHÔNG được thấy** trong danh sách untracked:
- `.env` (chứa email sale, đường dẫn nội bộ)
- `.venv/` (160MB+ packages)
- `data/inbox/`, `data/processed/`, `data/failed/`, `data/backup/`
- `*.xlsx` (file thật của khách hàng)
- `logs/`

**Phải thấy:** `CLAUDE.md`, `README.md`, `docs/`, `src/`, `tests/`, `.github/`, `.vscode/`, `.claude/`, `mkdocs.yml`, `pyproject.toml`, `requirements.txt`, `.env.example`, `.gitignore`, `.pre-commit-config.yaml`, `site_docs/`.

Nếu thấy `.venv/` hoặc `.env` → STOP, kiểm tra `.gitignore` trước.

---

## :material-numeric-5-circle: Stage + commit đầu tiên

```powershell
git add -A
git status --short
```

Quét output 1 lần nữa — không có file nhạy cảm.

```powershell
git commit -m "chore(repo): bootstrap project structure, docs, and website" -m "Phase 0 complete:
- CLAUDE.md auto-loop instructions for Claude Code
- docs/ (14 files: ARCHITECTURE, CODING_RULES, DATABASE, MAPPING, TECH_STACK, WORKFLOW, GIT_WORKFLOW, DECISIONS, GLOSSARY, TODO, TASKS, SETUP_VSCODE, FIRST_PUSH)
- src/auto_fill/ skeleton (config, mail, reader, mapper, filler, storage, utils)
- .vscode/ + .claude/ configs
- mkdocs.yml + site_docs/ (10 pages) for GitHub Pages
- .github/workflows/ (CI + deploy-docs)
- pyproject.toml, requirements.txt, .pre-commit-config.yaml

Refs: TODO #0.1 #0.2 #0.3 #0.4 #0.8 #0.9"
```

---

## :material-numeric-6-circle: Tag + push

```powershell
git tag -a v0.0.1-bootstrap -m "Phase 0: bootstrap complete"
git push -u origin main
git push origin v0.0.1-bootstrap
```

### Lần đầu push sẽ hỏi authentication

Có 2 cách (chọn 1):

=== "A. Git Credential Manager (khuyến nghị)"

    Browser sẽ tự popup → chọn **Sign in with your browser** → đăng nhập GitHub với `VietAnh954`.

    Sau khi xong, credential được lưu lại trong Windows. Push sau không hỏi nữa.

=== "B. Personal Access Token (PAT)"

    1. Vào https://github.com/settings/tokens → **Generate new token (classic)**.
    2. Note: `auto-fill-capdon-laptop`.
    3. Expiration: 90 days (hoặc tuỳ).
    4. Scope: tick `repo` (đủ).
    5. **Generate token** → copy chuỗi (chỉ hiện 1 lần).
    6. Quay lại PowerShell, khi `git push` hỏi password → **paste token** (không phải password GitHub).

---

## :material-numeric-7-circle: Verify lên GitHub đã có code

Mở: https://github.com/VietAnh954/Project_Autofill_capDon

Phải thấy:
- 1 commit "chore(repo): bootstrap..."
- 1 tag `v0.0.1-bootstrap`
- Cây thư mục đầy đủ.

---

## :material-numeric-8-circle: Enable GitHub Pages (cho web docs ở Phase 5)

Trên trang repo:

1. **Settings** (tab trên cùng, bên phải).
2. Bên trái menu → **Pages**.
3. **Build and deployment** → Source: chọn **GitHub Actions** (không phải "Deploy from a branch").
4. **Save** (nếu có nút).

Tiếp tục:

1. **Settings → Actions → General** (menu bên trái).
2. Kéo xuống mục **Workflow permissions**.
3. Chọn **Read and write permissions**.
4. Tick **Allow GitHub Actions to create and approve pull requests** (tuỳ chọn).
5. **Save**.

Khi Claude đẩy xong Phase 5 (build trang web), web tự deploy tới:
**https://vietanh954.github.io/Project_Autofill_capDon/**

---

## :material-check-all: :material-numeric-9-circle: Hoàn tất — gõ `go` trong Claude

Quay lại Claude Code panel trong VSCode → gõ:
```
go
```

Claude sẽ:
1. Đọc `CLAUDE.md` (đã có @import TODO.md + TASKS.md).
2. Lấy task `1.1` (đầu tiên chưa tick trong TODO.md).
3. Code → test → update TASKS.md → tick TODO → `git commit` → `git push origin main`.
4. Lặp đến hết Phase 1, tự `git tag v0.1.0-mvp-dulich && git push --tags`.

---

## :material-shield-bug-outline: Troubleshoot

??? failure ":material-close: `fatal: not a git repository`"

    Bạn đang ở sai folder. `cd` về đúng:
    ```powershell
    cd C:\Users\ADMIN\OneDrive\Company\Project_Autofill_capDon
    ```

??? failure ":material-close: `remote origin already exists`"

    Đã add remote rồi. Update URL thay vì add mới:
    ```powershell
    git remote set-url origin https://github.com/VietAnh954/Project_Autofill_capDon.git
    ```

??? failure ":material-close: `Updates were rejected because the remote contains work...`"

    Repo trên GitHub có sẵn file (thường là README/license tự sinh khi tạo repo).

    Cách an toàn — pull về rồi merge:
    ```powershell
    git pull origin main --allow-unrelated-histories
    # Có thể có conflict file README. Edit tay rồi:
    git add -A
    git commit -m "chore: merge initial GitHub README"
    git push -u origin main
    ```

    Cách nhanh (KHÔNG khuyên nếu repo trên GH có dữ liệu quý):
    ```powershell
    git push -u origin main --force-with-lease
    ```

??? failure ":material-close: Push bị reject vì file quá lớn"

    Có file > 100MB trong commit. GitHub không cho.

    Tìm file lớn:
    ```powershell
    git ls-files | ForEach-Object { [PSCustomObject]@{ File=$_; Size=(Get-Item $_).Length } } | Sort-Object Size -Descending | Select-Object -First 10
    ```

    Thường là `.venv/` lọt vào. Fix:
    ```powershell
    git rm -r --cached .venv
    git commit -m "chore: remove .venv from tracking"
    # Verify .gitignore có dòng ".venv/"
    git push -u origin main
    ```

??? failure ":material-close: `Authentication failed`"

    PAT đã hết hạn hoặc sai. Tạo lại:
    1. https://github.com/settings/tokens → revoke token cũ.
    2. Generate new token → scope `repo`.
    3. Clear credential cache:
       ```powershell
       git credential-manager erase
       # Nhập: protocol=https <Enter> host=github.com <Enter> <Enter>
       ```
    4. Push lại → nhập token mới.

??? failure ":material-close: GitHub Pages báo 404 sau khi enable"

    - Phase 5 chưa làm xong nên chưa có file `site/` build ra. Cần chờ Claude code Phase 5 (task 5.1 → 5.8).
    - Hoặc: workflow `deploy-docs.yml` chưa chạy. Vào tab **Actions** trên GitHub xem có job nào fail không.

??? failure ":material-close: `.claude/settings.json` báo "Invalid value" trong VSCode"

    Đã fix trong commit `chore: fix .claude/settings.json schema`. Đảm bảo bạn pull về phiên bản mới nhất.

---

## :material-arrow-right-bold-circle: Sau bước này

Mọi commit/push sau **Claude tự làm** trong auto-loop. Bạn không cần chạm git nữa, trừ khi:

- Cần xem lịch sử: `git log --oneline -20`
- Cần rollback: xem `docs/GIT_WORKFLOW.md §10`
- Cần đổi máy: clone về máy mới + làm lại từ `pip install -r requirements.txt`
