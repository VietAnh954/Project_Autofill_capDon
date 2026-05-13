# Auto-fill Cấp Đơn

> **Tự động hoá nhập liệu phiếu cấp đơn bảo hiểm từ Outlook vào file Excel tổng.**

[![GitHub](https://img.shields.io/badge/GitHub-VietAnh954%2FProject__Autofill__capDon-181717?logo=github)](https://github.com/VietAnh954/Project_Autofill_capDon)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: Internal](https://img.shields.io/badge/license-Internal-lightgrey)](#)

---

## :material-lightbulb-on: Tại sao có project này?

Hàng ngày, mỗi sale gửi email kèm file Excel/CSV chứa **phiếu cấp đơn bảo hiểm**
(du lịch, sức khỏe, ô tô, xe máy, BHYT/BHXH, HSSV, …).
Bạn phải tự mở từng file, copy-paste từng dòng vào file Excel tổng — **dễ sai sót, tốn 1-2 giờ/ngày**.

Auto-fill Cấp Đơn giải quyết:

- :material-email-fast: **Tự đọc mail** mới từ Outlook desktop.
- :material-download: **Tải attachment** vào folder local.
- :material-magnify-scan: **Phân loại** sản phẩm (du lịch / sức khỏe / xe máy…) theo sender + subject + cột.
- :material-translate: **Chuẩn hoá** dữ liệu (ngày, CCCD, số điện thoại, tiền tệ).
- :material-table-check: **Ghi vào sheet đúng** trong file Excel tổng — append-only, có dedup.
- :material-backup-restore: **Backup** tự động trước khi sửa.
- :material-file-document-check: **Log** từng record, **report** cuối ngày.

---

## :material-flash: Demo nhanh

=== "Trước (làm tay)"

    1. Mở Outlook → đọc 20 mail của 8 sale.
    2. Tải 20 file Excel khác nhau.
    3. Mở file tổng, scroll tới sheet đúng.
    4. Copy-paste 100+ dòng.
    5. Kiểm tra trùng lặp tay.
    6. Lưu file, backup.

    :material-clock-alert: **~90 phút/ngày**. :material-emoticon-sad: **Hay sai CCCD, ngày tháng**.

=== "Sau (auto)"

    ```powershell
    python -m auto_fill run
    ```

    :material-clock-fast: **~2 phút.** :material-check-decagram: **Sai sót giảm gần 0**.

---

## :material-rocket-launch-outline: Bắt đầu

<div class="grid cards" markdown>

-   :material-download-circle:{ .lg .middle } **Cài đặt**

    ---

    Hướng dẫn cài VSCode, Python, Claude Code và setup project trong 15 phút.

    [:octicons-arrow-right-24: Bắt đầu cài](installation.md)

-   :material-play-circle:{ .lg .middle } **Sử dụng**

    ---

    Quy trình chạy hằng ngày, lệnh thường dùng, cách handle lỗi.

    [:octicons-arrow-right-24: Hướng dẫn dùng](usage.md)

-   :material-cog-outline:{ .lg .middle } **Cách hoạt động**

    ---

    Sơ đồ flow chi tiết: Outlook → Reader → Mapper → Filler → Master.

    [:octicons-arrow-right-24: Xem flow](how-it-works.md)

-   :material-tools:{ .lg .middle } **Kỹ thuật**

    ---

    Kiến trúc, tech stack, danh sách sản phẩm BH được hỗ trợ.

    [:octicons-arrow-right-24: Tech details](architecture.md)

</div>

---

## :material-information: Thông tin nhanh

| Item | Giá trị |
|------|---------|
| Repo | [github.com/VietAnh954/Project_Autofill_capDon](https://github.com/VietAnh954/Project_Autofill_capDon) |
| OS hỗ trợ | Windows 10/11 (Outlook desktop bắt buộc) |
| Ngôn ngữ | Python 3.11+ |
| File tổng | `.xlsx` (20 sheet, ~10k+ row) |
| Sản phẩm hỗ trợ MVP | Du lịch, Sức khỏe, Ô tô, Xe máy, BHYT/BHXH, HSSV |
| License | Internal — không public |
