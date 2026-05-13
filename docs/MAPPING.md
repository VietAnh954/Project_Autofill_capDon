# MAPPING.md

> Quy tắc mapping field giữa **input** (file từ email) và **output** (file tổng).
> Claude PHẢI đọc file này TRƯỚC khi viết mapper / reader.

---

## 1. Tổng quan

Input có thể đến dưới nhiều dạng/cách đặt tên:
- File Excel/CSV do đại lý gửi, header tiếng Việt không chuẩn ("Họ tên KH", "ten kh", "Hovaten").
- File PDF (Phase 2) → OCR → parse.
- 1 mail có thể chứa nhiều phiếu cùng loại HOẶC nhiều loại cùng lúc.

Mục tiêu mapping: chuyển input → **canonical schema nội bộ** → ghi vào sheet đúng.

---

## 2. Canonical schema (cột chuẩn nội bộ)

Dùng tên cột chuẩn này trong DataFrame xuyên suốt pipeline (snake_case, English):

| Canonical name | Mô tả | Ví dụ |
|----------------|-------|-------|
| `issued_date` | Ngày cấp đơn / ngày update | 2026-05-14 |
| `insured_name` | Họ tên người được bảo hiểm (NĐBH) | NGUYỄN VĂN A |
| `insured_dob` | Ngày sinh NĐBH | 1990-01-15 |
| `insured_gender` | Giới tính | M / F |
| `insured_id_number` | CCCD/CMND/Passport | 012345678901 |
| `insured_phone` | SĐT NĐBH | 0901234567 |
| `insured_email` | Email NĐBH | a@x.com |
| `insured_address` | Địa chỉ NĐBH | ... |
| `buyer_name` | Bên mua BH (BMBH) | NGUYỄN VĂN B |
| `buyer_dob` | Ngày sinh BMBH | |
| `buyer_id_number` | CCCD BMBH | |
| `buyer_phone` | SĐT BMBH | |
| `buyer_relation` | Mối quan hệ BMBH↔NĐBH | Vợ/Chồng/Con/... |
| `contract_number` | Số hợp đồng | HD2026-001 |
| `effective_from` | Ngày bắt đầu hiệu lực | |
| `effective_to` | Ngày kết thúc hiệu lực | |
| `premium` | Phí bảo hiểm (VND, float) | 1500000.0 |
| `product_code` | Mã sản phẩm | TRAVEL-GL-IND |
| `plan` | Plan tham gia | Plan A |
| `scope` | Phạm vi | Toàn cầu |
| **Travel-specific** | | |
| `trip_start` / `trip_end` / `destination` / `trip_days` | | |
| **Vehicle-specific** | | |
| `plate_number` / `frame_number` / `engine_number` / `vehicle_brand` / `vehicle_type` / `vehicle_value` / `seats` / `usage_purpose` | | |
| **Health-specific** | | |
| `outpatient` / `dental` / `maternity` / `topup` / `adjustment_fee` | | |
| **HSSV-specific** | | |
| `school` / `class_name` | | |
| **Metadata** | | |
| `source_email_id` | Track gốc | |
| `source_attachment` | Tên file gốc | |

---

## 3. Normalization rules

### 3.1. Date
- Input chấp nhận: `dd/mm/yyyy`, `yyyy-mm-dd`, `dd-mm-yyyy`, Excel serial date.
- Output: `datetime.date`.
- Năm 2 chữ số (`14/05/26`): nếu < current_year+1 → 20xx, else 19xx.
- Fail parse → log + `failed/` (KHÔNG tự đoán).

### 3.2. CCCD / CMND / Passport
- Strip whitespace, uppercase.
- Validate length: CCCD = 12 chữ số, CMND cũ = 9 chữ số.
- Passport: alphanumeric, 6–9 ký tự (không cấm).
- Lưu vào `insured_id_number` không phân biệt loại — thêm cờ `id_type` nếu cần sau.

### 3.3. Phone
- Chuẩn output: bắt đầu `0`, 10 chữ số (mobile VN).
- `+84xxx` → `0xxx`.
- `84xxx` → `0xxx`.
- Strip dấu cách, gạch nối.

### 3.4. Money
- Input có thể là `"1,500,000"`, `"1.500.000 VND"`, `"1.5M"`, số thuần.
- Strip ký tự không phải số / dấu thập phân.
- VN dùng `.` làm thousand separator → cần phân biệt với decimal:
  - Nếu có cả `,` và `.` → `.` = thousand, `,` = decimal.
  - Nếu chỉ có `.` và độ dài phần sau `.` là 3 → thousand sep.
- Output: `float` VND.

### 3.5. Name (tên người)
- Strip + collapse whitespace.
- Không tự ý đổi case. Giữ nguyên user typed (thường UPPER trong ngành BH).

### 3.6. Plate number (biển số xe)
- Uppercase. Strip dấu cách, dấu chấm thừa.
- Format chuẩn: `XX[X]-[X]NNN.NN` hoặc `XX-NNNN`. Giữ dấu `-` và `.` nếu có.

---

## 4. Field map: input headers → canonical

Đại lý đặt tên cột rất khác nhau. Mapper dùng **fuzzy match** (Levenshtein ratio > 0.85)
HOẶC bảng alias dưới đây (priority: alias > fuzzy):

```yaml
# src/auto_fill/mapper/aliases.yaml (sẽ tạo ở task 2.3)

insured_name:
  - "họ và tên"
  - "ho va ten"
  - "ten khach hang"
  - "tên khách hàng"
  - "ho ten ndbh"
  - "họ tên người được bảo hiểm"
  - "tên người được bh"
  - "tên ndbh"

insured_id_number:
  - "cccd"
  - "cmnd"
  - "cccd/cmnd"
  - "cccd/cmnd/passport"
  - "cccd/cmnd/paspost id"
  - "số cccd"

insured_dob:
  - "ngày sinh"
  - "ngay sinh"
  - "ngày tháng năm sinh"
  - "dob"

premium:
  - "phí bảo hiểm"
  - "phi bao hiem"
  - "tổng phí"
  - "tổng phí bảo hiểm"
  - "phí"

plate_number:
  - "biển số"
  - "biển số xe"
  - "bien so"
  - "bks"

# ... (tiếp tục cho mỗi canonical field)
```

---

## 5. Classifier: chọn sheet đích

`mapper/classifier.py` quyết định ghi vào sheet nào theo PRIORITY:

1. **Sender allowlist** trong `.env`:
   ```
   SENDER_DULICH=dulich@pti.com.vn
   SENDER_OTO=oto@pti.com.vn
   ```
2. **Subject keyword** (case-insensitive, có dấu hoặc không):

| Keyword in subject | → Sheet |
|--------------------|---------|
| "du lịch", "travel" | `Du lịch` |
| "sức khỏe", "health", "sk" | `Sức khỏe` |
| "ô tô", "oto", "auto", "car" | `Bao hiem oto` |
| "xe máy", "xe may", "tnds xm" | `Thông tin cấp Bảo hiểm xe máy` |
| "bhyt", "bhxh" | `BHYTBHXH` |
| "hssv", "học sinh", "sinh viên" | `HSSV` |
| "huỷ", "huy", "cancel" | `Hủy` |
| "hoàn phí", "hoan phi", "refund" | `Hoàn phí` |
| "nhà", "home" | `Nhà` |

3. **Column signature**: nếu input có cột `Biển số` + `Số khung` → vehicle.
   Phân biệt ô tô/xe máy qua cột `Số chỗ ngồi` (ô tô) hoặc `Loại xe` chứa "xe máy".

4. **Fallback**: hỏi user (trong chat / log warning, đẩy `failed/unclassified/`).

---

## 6. Mapping per-sheet (cột canonical → cột target)

### 6.1. Sheet `Du lịch`

| Canonical | → Target column (1-indexed) | Notes |
|-----------|---|---|
| `issued_date` | 1 (Ngày) | |
| (auto-STT) | 2 | `max(STT)+1` |
| `insured_name` | 3 (Họ Và Tên) | |
| `insured_dob` | 4 | |
| `insured_id_number` | 5 | |
| `effective_from` | 6 (Ngày thanh toán) | có thể là payment date |
| `trip_start` | 7 | |
| `trip_end` | 8 | |
| `trip_days` | 9 | compute |
| `destination` | 10 | |
| `scope` | 11 | |
| `plan` | 13 | |
| `premium` | 14 | |
| `buyer_name` | 15 | |

### 6.2. Sheet `Bao hiem oto`

| Canonical | → Col | Notes |
|-----------|---|---|
| `issued_date` | 1 | |
| (STT) | 2 | |
| `insured_name` (hoặc buyer_name nếu khác) | 3 | |
| `insured_phone` | 4 | |
| `insured_email` | 5 | |
| `insured_address` | 6 | |
| `plate_number` | 7 | dedup |
| `frame_number` | 8 | |
| `engine_number` | 9 | |
| `vehicle_load` | 10 | xe tải |
| `seats` | 11 | |
| `vehicle_type` | 12 | |
| `vehicle_brand` | 13 | |
| `vehicle_value` | 14 | |
| `usage_purpose` | 15 | |

### 6.3. Sheet `Thông tin cấp Bảo hiểm xe máy`

| Canonical | → Col |
|-----------|---|
| `issued_date` | 1 (Ngày update) |
| (STT) | 2 |
| `plate_number` | 3 |
| `frame_number` | 4 |
| `engine_number` | 5 |
| `insured_name` | 6 |
| `premium_tnds` | 7 |
| `premium_accident` | 8 |
| `years` | 9 |
| `premium` (total) | 10 |
| `effective_from` | 12 |
| `effective_to` | 13 |
| `vehicle_type` | 14 |
| `vehicle_brand` | 15 |

### 6.4. Sheet `Sức khỏe` (header row 3)

| Canonical | → Col |
|-----------|---|
| `issued_date` | 1 |
| (STT) | 2 |
| `insured_name` | 3 |
| `insured_dob` | 4 |
| `insured_gender` | 5 |
| `insured_email` | 6 |
| `insured_passport` | 7 |
| `insured_id_number` | 8 |
| `insured_address` | 9 |
| `buyer_name` | 10 |
| ... | ... |

### 6.5. Sheet `BHYTBHXH`

| Canonical | → Col |
|-----------|---|
| `issued_date` | 1 |
| (STT) | 2 |
| `insured_name` | 3 |
| `insured_dob` | 4 |
| `insured_gender` | 5 |
| `insured_id_number` | 6 |
| `insured_address` | 7 |
| `insured_phone` | 8 |
| `insured_email` | 9 |
| `buyer_name` | 10 |
| `buyer_dob` | 11 |
| `buyer_id_number` | 12 |
| `buyer_relation` | 13 |

### 6.6. Sheet `HSSV`

| Canonical | → Col |
|-----------|---|
| `issued_date` | 1 |
| `insured_name` | 2 |
| `insured_dob` | 3 |
| `insured_gender` | 4 |
| `insured_id_number` | 5 |
| `insured_email` | 6 |
| `insured_phone` | 7 |
| `insured_address` | 8 |
| `school` | 9 |
| `class_name` | 10 |
| `buyer_name` | 11 |
| `buyer_relation` | 12 |

---

## 7. Ví dụ end-to-end

**Input** (email subject: "Phiếu cấp đơn du lịch tháng 5"):
```csv
ho_ten,ngay_sinh,cmnd,ngay_di,ngay_ve,noi_den,phi
Nguyen Van A,15/01/1990,012345678,01/06/2026,07/06/2026,Singapore,1500000
```

**Sau parse + normalize:**
```python
{
  "issued_date": date(2026, 5, 14),
  "insured_name": "Nguyen Van A",
  "insured_dob": date(1990, 1, 15),
  "insured_id_number": "012345678",
  "trip_start": date(2026, 6, 1),
  "trip_end": date(2026, 6, 7),
  "trip_days": 7,
  "destination": "Singapore",
  "premium": 1500000.0,
  "source_email_id": "AAMkAD...",
  "source_attachment": "phieu_dulich_T5.csv",
}
```

**Sau classify:** `sheet = "Du lịch"`

**Sau fill:** dòng mới append vào sheet `Du lịch`, STT tự tăng, cột 1=14/05/2026, cột 3=Nguyen Van A, ...

---

## 8. Khi schema input chưa biết

Reader gặp file lạ (header không match alias, không classify được):
1. Lưu nguyên file vào `data/failed/unknown_schema/`.
2. Log warning với danh sách cột.
3. Thêm 1 entry "OPEN QUESTION" vào `docs/TASKS.md` để user review.
4. KHÔNG tự đoán mapping.
