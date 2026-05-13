# Cài đặt

!!! info "Thời gian"
    Khoảng 15-20 phút cho lần đầu. Sau đó setup máy mới chỉ ~5 phút.

## :material-package-down: 1. Phần mềm cần có

| Phần mềm | Phiên bản | Link |
|----------|-----------|------|
| Windows | 10 / 11 | — |
| Outlook Desktop | bất kỳ phiên bản có sẵn | — |
| [Visual Studio Code](https://code.visualstudio.com/) | mới nhất | [Tải](https://code.visualstudio.com/) |
| [Python](https://www.python.org/) | 3.11 hoặc 3.12 | [Tải](https://www.python.org/downloads/) |
| [Git for Windows](https://git-scm.com/download/win) | mới nhất | [Tải](https://git-scm.com/download/win) |
| Extension **Claude Code** | mới nhất | Cài trong VSCode |

!!! warning "Khi cài Python"
    Nhớ **TICK** ô `Add Python to PATH` ở màn hình đầu tiên.

## :material-folder-download: 2. Lấy code về máy

=== "Clone từ GitHub (khuyến nghị)"

    ```powershell
    cd C:\Users\ADMIN\OneDrive\Company
    git clone https://github.com/VietAnh954/Project_Autofill_capDon.git
    cd Project_Autofill_capDon
    code .
    ```

=== "Đã có folder local"

    ```powershell
    cd C:\Users\ADMIN\OneDrive\Company\Project_Autofill_capDon
    code .
    ```

## :material-cog-outline: 3. Setup Python environment

Trong terminal VSCode (`` Ctrl+` ``):

```powershell
# Tạo virtual environment
python -m venv .venv

# Kích hoạt
.venv\Scripts\Activate.ps1

# Nếu PowerShell block:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Cài dependencies
pip install -r requirements.txt
pip install -e .

# Cài pre-commit hook
pre-commit install

# Test
pytest -q
```

Kết quả mong đợi: **3 test pass**.

## :material-file-document-edit-outline: 4. Cấu hình `.env`

```powershell
copy .env.example .env
notepad .env
```

Sửa 3 mục quan trọng:

```ini
MASTER_FILE_PATH=C:\Users\ADMIN\OneDrive\Company\Project_Autofill_capDon\data\master\master.xlsx

# Liệt kê email các sale gửi phiếu (cách nhau dấu phẩy)
SENDER_ALLOWLIST=sale.hoa@pti.com.vn,sale.minh@pti.com.vn,sale.lan@pti.com.vn

OUTLOOK_PROFILE=Outlook
```

## :material-microsoft-excel: 5. Copy file Excel tổng

Copy file `Danh sách cấp đơn Offline PTI (3).xlsx` của bạn vào:

```
data\master\master.xlsx
```

(Đường dẫn này phải khớp với `MASTER_FILE_PATH` trong `.env`.)

## :material-github: 6. Setup Git + push lên GitHub (1 lần)

```powershell
git init
git branch -M main
git config user.name "VietAnh954"
git config user.email "nguyenvietanh92tn@gmail.com"
git remote add origin https://github.com/VietAnh954/Project_Autofill_capDon.git

git add -A
git commit -m "chore(repo): bootstrap project structure and docs"
git push -u origin main
```

!!! tip "Lần đầu push sẽ hỏi auth"
    - **Cách A (khuyến nghị):** Git Credential Manager — browser popup, đăng nhập GitHub → xong.
    - **Cách B:** Personal Access Token — vào `github.com → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new → scope: repo`. Khi push hỏi password → paste token.

## :material-web-check: 7. Enable GitHub Pages (cho web docs)

Sau khi push lần đầu:

1. Vào https://github.com/VietAnh954/Project_Autofill_capDon
2. **Settings** → **Pages**
3. Source: **GitHub Actions**
4. **Save**
5. **Settings → Actions → General → Workflow permissions** → chọn **Read and write permissions** → **Save**

Sau khi Claude hoàn thành Phase 5, push lên main → web tự build và live tại:
`https://vietanh954.github.io/Project_Autofill_capDon/`

## :material-check-all: 8. Verify tất cả OK

Trong VSCode terminal:

```powershell
# Kiểm tra mọi thứ
.venv\Scripts\Activate.ps1
python -c "from auto_fill.config import settings; print('Master:', settings.master_file_path)"
pytest -q
git status
git log --oneline -3
```

Nếu cả 3 lệnh cuối chạy OK → :material-party-popper: **sẵn sàng dùng**.

## :material-arrow-right-circle: Tiếp theo

Đọc [Hướng dẫn sử dụng](usage.md) để biết quy trình chạy hằng ngày.
