# Khắc phục sự cố

## :material-email-alert-outline: Outlook / Mail

??? failure "RPC_E_DISCONNECTED khi connect Outlook"

    **Nguyên nhân:** Outlook chưa mở.

    **Cách xử:** Mở Outlook app trước → đợi sync xong → chạy lại pipeline.

    Hoặc set trong `.env`:
    ```ini
    OUTLOOK_AUTO_START=true
    ```

??? failure "Mail không được fetch dù có mail mới"

    **Check:**

    1. Sender email có trong `SENDER_ALLOWLIST` không?
        ```powershell
        type .env | Select-String "SENDER_ALLOWLIST"
        ```
    2. Subject có match `SUBJECT_PATTERN` không?
        ```powershell
        python -c "import re; print(bool(re.search(r'(?i)c[aâ]p\s*[đd][oơ]n', 'Phieu cap don du lich')))"
        ```
    3. Mail có ở `OUTLOOK_INBOX_FOLDER` không (mặc định `Inbox`)?

??? failure "Mail đã processed rồi vẫn fetch lại"

    **Nguyên nhân:** Pipeline crashed giữa chừng, chưa mark Read.

    **Cách xử:** Lần sau chạy `run`, pipeline sẽ tự dedup theo `(CCCD, Ngày đi, ...)`. Không lo ghi đôi vào master.

## :material-microsoft-excel: File tổng (Master Excel)

??? failure "Permission denied khi ghi master.xlsx"

    **Nguyên nhân:** File đang mở trong Excel.

    **Cách xử:** Đóng Excel → chạy lại. Pipeline có retry 3 lần (10s mỗi lần).

??? failure "Sheet "Sức khỏe" báo header row không đúng"

    **Nguyên nhân:** Sheet này có header ở row 3 chứ không phải row 1.

    **Cách xử:** Đã có trong `src/auto_fill/config/sheet_registry.py` (`header_row=3`).
    Nếu vẫn lỗi → check sheet có bị format lại không.

??? failure "Master file bị mất formula sau khi pipeline ghi"

    **Cách xử:**

    1. Restore từ backup: `data\backup\<date>\master_HH-MM-SS.xlsx`.
    2. Mở `src/auto_fill/filler/excel_writer.py` → đảm bảo dùng `load_workbook(path, data_only=False)`.

## :material-language-python: Python / Dependencies

??? failure "pywin32 không import được"

    ```powershell
    # Chạy PowerShell as Administrator
    python -m pywin32_postinstall -install
    ```

??? failure "pip install fail vì SSL / proxy"

    ```powershell
    pip install -r requirements.txt --index-url https://pypi.org/simple --trusted-host pypi.org --trusted-host files.pythonhosted.org
    ```

??? failure "pytest "module not found: auto_fill""

    **Nguyên nhân:** Quên `pip install -e .`.

    **Cách xử:**
    ```powershell
    .venv\Scripts\Activate.ps1
    pip install -e .
    ```

## :material-github: Git / GitHub

??? failure "git push bị reject vì authentication failed"

    **Cách xử (chọn 1):**

    **A. Git Credential Manager:**
    ```powershell
    git config --global credential.helper manager
    git push origin main
    # → browser popup → login GitHub
    ```

    **B. Personal Access Token:**
    1. github.com → Settings → Developer settings → Personal access tokens → Tokens (classic).
    2. Generate new token → scope `repo` → copy.
    3. Khi push hỏi password → paste token.

??? failure "git push bị reject vì non-fast-forward"

    Có commit trên remote mà local chưa pull:
    ```powershell
    git pull --rebase origin main
    git push origin main
    ```

??? failure "Nhỡ commit .env / file data lên GitHub"

    !!! danger "Quan trọng"
        Token / email khách hàng đã leak. Xử lý ngay:

    ```powershell
    # 1. Xoá file khỏi git history (cài git-filter-repo)
    pip install git-filter-repo
    git filter-repo --path .env --invert-paths
    git push --force origin main

    # 2. Đổi token / password đã lộ
    # 3. Liên hệ GitHub Support yêu cầu purge cache
    ```

## :material-robot-confused-outline: Claude Code

??? failure "Claude không đọc CLAUDE.md"

    **Check:**
    ```powershell
    type .claude\settings.json | Select-String "alwaysIncludeFiles"
    ```

    Phải có:
    ```json
    "context": {
      "alwaysIncludeFiles": ["CLAUDE.md", "docs/TODO.md", "docs/TASKS.md"]
    }
    ```

    Nếu chưa → reload VSCode window (`Ctrl+Shift+P` → "Reload Window").

??? failure "Claude làm sai task / lạc khỏi TODO.md"

    1. Gõ `stop`.
    2. Mở `docs/TASKS.md` → revert manual.
    3. `git reset --hard <commit-hash-cuối-đúng>`.
    4. Gõ `/status` để Claude re-orient.
    5. Gõ `go`.

??? failure "Claude xài hết token nhanh"

    Đọc `docs/SETUP_VSCODE.md` mục 7 — tips tối ưu token:

    - Mỗi doc < 500 dòng.
    - `docs/TASKS.md` chỉ giữ 5 entry gần nhất.
    - Reset session khi context > 70%.
    - Dùng `/status` thay vì hỏi free-text.

## :material-web: GitHub Pages / Web docs

??? failure "Web https://vietanh954.github.io/Project_Autofill_capDon/ trả 404"

    **Check:**

    1. Settings → Pages → Source = **GitHub Actions** (không phải "Deploy from branch").
    2. Settings → Actions → General → Workflow permissions = **Read and write**.
    3. Vào tab **Actions** xem workflow `deploy-docs` có chạy xanh không.

??? failure "Mermaid diagram không render"

    **Check:** `mkdocs.yml` có `pymdownx.superfences` với custom fence cho mermaid và plugin `mermaid2` chưa.

## :material-help-network-outline: Vẫn không xử được?

1. Tìm trong **GitHub Issues**: https://github.com/VietAnh954/Project_Autofill_capDon/issues
2. Mở issue mới với:
   - Lệnh đã chạy.
   - Output / error đầy đủ.
   - Phiên bản Python, Windows, Outlook.
   - File log gần nhất (đã che CCCD/email khách hàng).
