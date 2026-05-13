# GLOSSARY.md — Từ điển domain (bảo hiểm) & viết tắt

> Khi Claude gặp từ lạ trong file/email → tra ở đây trước khi đoán.

---

## Bảo hiểm — viết tắt phổ biến

| Viết tắt | Nghĩa đầy đủ | Tiếng Anh tương ứng |
|----------|--------------|---------------------|
| NĐBH | Người được bảo hiểm | Insured |
| BMBH | Bên mua bảo hiểm | Policyholder / Buyer |
| HĐBH | Hợp đồng bảo hiểm | Insurance contract / Policy |
| TNDS | Trách nhiệm dân sự | Civil liability (compulsory motor) |
| NNTX | Người ngồi trên xe | Passenger (in vehicle) |
| BHYT | Bảo hiểm y tế | Health insurance (state) |
| BHXH | Bảo hiểm xã hội | Social insurance |
| BHTN | Bảo hiểm thất nghiệp | Unemployment insurance |
| BH | Bảo hiểm | Insurance |
| HSSV | Học sinh sinh viên | Students (school insurance) |
| VAS | Value-added Service | Dịch vụ giá trị gia tăng |
| TPA | Third-Party Administrator | Đơn vị xử lý bồi thường thay |
| CCCD | Căn cước công dân (12 số) | National ID |
| CMND | Chứng minh nhân dân (9 số, cũ) | Old national ID |

---

## Sản phẩm trong file tổng

| Sheet name | Sản phẩm | Sheet alias trong code |
|------------|----------|------------------------|
| Du lịch | BH du lịch | `travel` |
| Sức khỏe | BH sức khỏe (cá nhân/gia đình/group) | `health` |
| Bao hiem oto | BH ô tô (thân vỏ + TNDS) | `auto` |
| Thông tin cấp Bảo hiểm xe máy | BH xe máy (TNDS bắt buộc + NNTX) | `motorbike` |
| BHYTBHXH | BH y tế + xã hội | `bhyt_bhxh` |
| HSSV | BH học sinh sinh viên | `student` |
| Hủy | Đơn đã huỷ | `cancellation` |
| Hoàn phí | Hoàn lại phí | `refund` |
| Nhà | BH nhà ở | `home` |
| Bảo hiểm rủi ro | BH rủi ro tài sản / kỹ thuật | `risk` |
| Trách nhiệm sản phẩm | BH trách nhiệm sản phẩm | `product_liability` |
| Cap the | Cấp thẻ BH | `card_issuance` |
| Thông tin thẻ | Thông tin thẻ BH | `card_info` |
| SỬA ĐỔI | Sửa đổi hợp đồng | `endorsement` |
| Chi bù | Chi bù phí | `topup_payment` |
| sản phẩm | Catalogue sản phẩm | `product_catalog` |
| VAS | Dịch vụ giá trị gia tăng | `vas` |
| Tracking sản phẩm | Tracking trạng thái | `tracking` |
| TEMPLATE | Template gốc | `template` |
| Bản sao của Trang tính1 | Tab backup | `backup` |

---

## Thuật ngữ kỹ thuật trong code

| Từ | Nghĩa |
|----|-------|
| Canonical schema | Tên cột chuẩn nội bộ DataFrame (English snake_case) |
| Alias | Biến thể tên cột mà mapper accept |
| Dedup key | Tổ hợp cột dùng để check trùng |
| Master file | File tổng `Danh sách cấp đơn Offline PTI.xlsx` |
| Inbox / Processed / Failed | Folder con của `data/` cho 3 trạng thái attachment |
| Auto-loop | Vòng lặp Claude tự chạy task theo TODO.md |
| Blocker | Tình huống dừng auto-loop chờ user |

---

## Đơn vị tiền

- Tất cả tiền trong file tổng là **VND** (đồng).
- Đôi khi file đại lý ghi `"1.5 tr"` (triệu) → normalizer xử lý:
  - `tr` / `triệu` → `* 1_000_000`.
  - `k` / `nghìn` → `* 1_000`.
  - `M` (capital, USD context) → KHÔNG tự convert, đẩy fail (ngừa nhầm tệ).

---

## Format ngày tiếng Việt

- `dd/mm/yyyy` là chuẩn VN, **KHÁC** US (`mm/dd/yyyy`).
- File Excel có thể lưu serial date (số). Normalizer dùng `openpyxl` epoch để parse.

---

## Quy ước họ tên

- Trong ngành BH VN, họ tên thường viết HOA toàn bộ (vd `NGUYỄN VĂN A`).
- Reader KHÔNG tự đổi case — giữ nguyên user typed.
