# Sản phẩm bảo hiểm hỗ trợ

File Excel tổng `Danh sách cấp đơn Offline PTI.xlsx` có **20 sheet**.
Pipeline hỗ trợ dần theo Phase.

## :material-rocket: MVP (Phase 1)

| Sheet | Sản phẩm | Header row | Dedup key |
|-------|----------|-----------:|-----------|
| **Du lịch** | BH du lịch | 1 | (CCCD, Ngày đi, Nơi đến) |

## :material-rocket-launch: Phase 2 (6 sản phẩm chính)

| Sheet | Sản phẩm | Header row | Dedup key |
|-------|----------|-----------:|-----------|
| Du lịch | BH du lịch | 1 | (CCCD, Ngày đi, Nơi đến) |
| Sức khỏe | BH sức khỏe | 3 | (CCCD, Ngày hiệu lực) |
| Bao hiem oto | BH ô tô | 1 | (Biển số, Ngày cấp đơn) |
| Thông tin cấp Bảo hiểm xe máy | BH xe máy TNDS | 2 | (Biển số xe, Ngày cấp đơn) |
| BHYTBHXH | BH y tế / xã hội | 2 | (CCCD, Loại BH, Năm hiệu lực) |
| HSSV | BH học sinh sinh viên | 1 | (CCCD, Năm học) |

## :material-database-plus: Phase 2 mở rộng (14 sheet còn lại)

Các sheet còn lại sẽ thêm dần theo nhu cầu user:

- TEMPLATE (template gốc)
- Thông tin thẻ (phát hành thẻ BH)
- SỬA ĐỔI (endorsement)
- Hủy (cancellation)
- Bảo hiểm rủi ro (risk)
- Chi bù (topup payment)
- sản phẩm (catalogue)
- Trách nhiệm sản phẩm (product liability)
- VAS (value-added service)
- Hoàn phí (refund)
- Cap the (card issuance)
- Bản sao của Trang tính1 (backup tab)
- Nhà (BH nhà ở)
- Tracking sản phẩm

## :material-translate: Mapping field

Mỗi sheet có schema riêng, nhưng pipeline dùng **canonical schema nội bộ** (English snake_case).
Khi mỗi sale gửi file có header khác nhau, mapper dùng:

1. **Alias lookup** (priority): `aliases.yaml` ánh xạ `"ho ten ndbh"` → `insured_name`.
2. **Fuzzy match** (fallback): rapidfuzz ratio > 0.85.

Ví dụ canonical fields chính:

```
insured_name       — Họ tên người được BH
insured_dob        — Ngày sinh NĐBH
insured_id_number  — CCCD/CMND/Passport
insured_phone      — SĐT
insured_email      — Email
buyer_name         — Bên mua BH (BMBH)
contract_number    — Số hợp đồng
effective_from     — Ngày bắt đầu hiệu lực
effective_to       — Ngày kết thúc
premium            — Phí (VND)
plan / scope       — Plan / phạm vi
```

Sản phẩm cụ thể có thêm field:

- **Vehicle:** `plate_number`, `frame_number`, `engine_number`, `vehicle_brand`, …
- **Travel:** `trip_start`, `trip_end`, `destination`, `trip_days`
- **Health:** `outpatient`, `dental`, `maternity`, `topup`
- **HSSV:** `school`, `class_name`

Đầy đủ: [MAPPING.md](https://github.com/VietAnh954/Project_Autofill_capDon/blob/main/docs/MAPPING.md).
