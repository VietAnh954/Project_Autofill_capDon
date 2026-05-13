# DATABASE.md

> Mô tả "kho dữ liệu" của dự án: file Excel tổng hiện tại + thiết kế DB tương lai.
> Đọc file này TRƯỚC khi viết bất kỳ code đụng tới schema.

---

## 1. Nguồn dữ liệu hiện tại (Phase 1)

**File:** `data/master/Danh sách cấp đơn Offline PTI.xlsx`
(người dùng tải về từ Google Sheet, lưu local để test)

**Tổng quan:** 20 sheets, mỗi sheet là 1 loại sản phẩm bảo hiểm.
Mỗi dòng = 1 hợp đồng / phiếu cấp đơn đã nhập.

| # | Sheet name | Loại sản phẩm | Số cột | Ước số hàng | Header row |
|---|------------|---------------|--------|-------------|------------|
| 1  | `TEMPLATE ` (có space) | Template gốc | 43 | 1005 | 2 |
| 2  | `Thông tin thẻ` | Phát hành thẻ BH | — | — | — |
| 3  | `SỬA ĐỔI` | Sửa đổi hợp đồng | — | — | — |
| 4  | `Du lịch` | BH du lịch | 30 | 1011 | 1 |
| 5  | `Sức khỏe` | BH sức khỏe | 57 | 10191 | 3 |
| 6  | `Bao hiem oto` | BH ô tô | 34 | 1005 | 1 |
| 7  | `BHYTBHXH` | BH y tế / xã hội | — | — | 2 |
| 8  | `Thông tin cấp Bảo hiểm xe máy` | BH xe máy | 54 | 3062 | 2 |
| 9  | `Hủy` | Đơn huỷ | — | — | 1 |
| 10 | `Bảo hiểm rủi ro` | BH rủi ro | — | — | — |
| 11 | `Chi bù` | Chi bù phí | — | — | — |
| 12 | `sản phẩm` | Catalogue SP | — | — | — |
| 13 | `Trách nhiệm sản phẩm` | BH TN sản phẩm | — | — | — |
| 14 | `VAS` | VAS | — | — | — |
| 15 | `Hoàn phí` | Hoàn phí | — | — | 1 |
| 16 | `HSSV` | BH học sinh sinh viên | — | — | 1 |
| 17 | `Cap the` | Cấp thẻ | — | — | — |
| 18 | `Bản sao của Trang tính1` | Backup tab | — | — | — |
| 19 | `Nhà` | BH nhà ở (export từ TPA) | — | — | 1 |
| 20 | `Tracking sản phẩm` | Tracking | — | — | — |

**Lưu ý quan trọng:**
- Header row KHÔNG nhất quán giữa các sheet (1, 2, hoặc 3) → reader phải tự detect.
- Một số sheet có **2 hàng header gộp** (merged cell ở row trên).
- Tên cột có thể chứa `\n` (xuống dòng) — cần `.strip()` khi so khớp.
- Sheet `TEMPLATE ` có space ở cuối tên — phải dùng đúng tên.

---

## 2. Schema chi tiết (top 6 sheet ưu tiên cho MVP)

### 2.1. Sheet `Du lịch` (header row 1)

| Col | Header | Type | Required | Note |
|-----|--------|------|----------|------|
| 1 | Ngày | date | yes | Ngày cấp đơn |
| 2 | STT | int | yes | Auto-increment |
| 3 | Họ Và Tên | str | yes | Người được BH |
| 4 | Ngày sinh | date | yes | dd/mm/yyyy |
| 5 | CCCD/CMND/Paspost ID | str | yes | Key dedup |
| 6 | Ngày thanh toán | date | no | |
| 7 | Ngày đi | date | yes | |
| 8 | Ngày về | date | yes | |
| 9 | Số ngày | int | computed | = Ngày về - Ngày đi |
| 10 | Nơi đến | str | yes | Quốc gia |
| 11 | Phạm vi | str | yes | Toàn cầu / Châu Á |
| 12 | Gói tham gia | str | yes | Cá nhân / Gia đình |
| 13 | Plan tham gia | str | yes | |
| 14 | Phí bảo hiểm | money | yes | VND |
| 15 | Họ tên người mua | str | yes | Bên mua BH (BMBH) |
| ... | ... | ... | ... | (tiếp đến cột 30) |

### 2.2. Sheet `Bao hiem oto` (header row 1)

| Col | Header | Type | Required |
|-----|--------|------|----------|
| 1 | (ngày) | date | yes |
| 2 | STT | int | yes |
| 3 | Tên khách hàng | str | yes |
| 4 | Số điện thoại | str | yes |
| 5 | email | str | no |
| 6 | địa chỉ | str | yes |
| 7 | Biển số | str | yes — **dedup key** |
| 8 | Số Khung | str | yes |
| 9 | Số Máy | str | yes |
| 10 | Trọng tải đối với xe tải | float | conditional |
| 11 | Số chỗ ngồi | int | yes |
| 12 | Loại xe | str | yes |
| 13 | Hiệu xe | str | yes |
| 14 | Giá trị xe | money | yes |
| 15 | Mục đích sử dụng | str | yes |

### 2.3. Sheet `Thông tin cấp Bảo hiểm xe máy` (header row 2)

| Col | Header | Type |
|-----|--------|------|
| 1 | Ngày update | date |
| 2 | STT | int |
| 3 | BIỂN SỐ XE | str — **dedup key** |
| 4 | SỐ KHUNG | str |
| 5 | SỐ MÁY | str |
| 6 | TÊN KHÁCH HÀNG | str |
| 7 | PHÍ BẢO HIỂM TNDS BẮT BUỘC | money |
| 8 | PHÍ BẢO HIỂM TAI NẠN NNTX | money |
| 9 | SỐ NĂM | int |
| 10 | TỔNG PHÍ BẢO HIỂM | money — `=col7+col8` |
| 11 | NGÀY CẤP ĐƠN | date |
| 12 | NGÀY BẮT ĐẦU | date |
| 13 | NGÀY KẾT THÚC | date — `=col12 + (col9 năm)` |
| 14 | LOẠI XE | str |
| 15 | NHÃN HIỆU XE | str |

### 2.4. Sheet `Sức khỏe` (header row 3, có gộp cell row 2)

Row 2 là grouping header:
- Col 5–9: **THÔNG TIN NGƯỜI ĐƯỢC BẢO HIỂM**
- Col 10–16: **THÔNG TIN BÊN MUA BẢO HIỂM**
- Col 17+: **THÔNG TIN HỢP ĐỒNG**

Row 3 mới là tên cột thật:
| Col | Header (row 3) | Type |
|-----|----------------|------|
| 1 | Ngày cập nhật | date |
| 2 | STT | int |
| 3 | Thông tin Người được bảo hiểm | str (họ tên) |
| 4 | Ngày tháng năm sinh | date |
| 5 | Giới tính | str |
| 6 | Email | str |
| 7 | Passport | str |
| 8 | CCCD | str — **dedup key** |
| 9 | Địa chỉ | str |
| 10 | Thông tin Bên mua bảo hiểm | str |
| ... | (đến cột 57) | ... |

### 2.5. Sheet `BHYTBHXH` (header row 2)

| Col | Header |
|-----|--------|
| 1 | Ngày update |
| 2 | STT |
| 3 | Họ tên NĐBH |
| 4 | Ngày sinh |
| 5 | Giới tính |
| 6 | CCCD |
| 7 | Địa chỉ |
| 8 | SĐT |
| 9 | Email |
| 10 | Họ tên BMBH |
| 11 | Ngày sinh (BMBH) |
| 12 | CCCD (BMBH) |
| 13 | Mối quan hệ với NĐBH |
| ... | ... |

### 2.6. Sheet `HSSV` (học sinh sinh viên, header row 1)

| Col | Header |
|-----|--------|
| 1 | Ngày update |
| 2 | Tên người được BH |
| 3 | Ngày sinh |
| 4 | Giới tính |
| 5 | CCCD/CMND/Passport |
| 6 | Email |
| 7 | Số đt |
| 8 | Địa chỉ |
| 9 | Trường |
| 10 | Lớp |
| 11 | Người yêu cầu BH (BMBH) |
| 12 | Mối quan hệ với NĐBH |
| ... | ... |

---

## 3. Convention chung khi append dòng mới

1. **STT** auto = `max(STT cũ) + 1`, tính trong phạm vi sheet đó.
2. **Ngày update / Ngày cấp đơn**: `today()` nếu input không có.
3. **Format date**: lưu kiểu `datetime`, KHÔNG lưu chuỗi.
4. **Format money**: số float, đơn vị VND, KHÔNG kèm "đ" / "VND" / dấu chấm.
5. **CCCD / Biển số**: chuẩn hoá UPPERCASE, bỏ khoảng trắng thừa.
6. **Phone**: prefix `+84` hoặc giữ `0...` — chọn 1 (xem MAPPING.md §3).

---

## 4. Dedup keys (mỗi sheet 1 key set)

| Sheet | Dedup key |
|-------|-----------|
| Du lịch | (CCCD, Ngày đi, Nơi đến) |
| Sức khỏe | (CCCD, Ngày hiệu lực) |
| Bao hiem oto | (Biển số, Ngày cấp đơn) |
| Xe máy | (BIỂN SỐ XE, NGÀY CẤP ĐƠN) |
| BHYTBHXH | (CCCD NĐBH, Loại BH, Năm hiệu lực) |
| HSSV | (CCCD, Năm học) |
| Hủy / Hoàn phí | (Số hợp đồng gốc) |

Gặp dup → KHÔNG ghi, đẩy vào `data/failed/duplicates/`.

---

## 5. Roadmap DB (Phase 3)

Khi user OK chuyển sang DB:

```
SQLite (file local) → Postgres (server)
```

Schema khởi điểm (1 table / sheet hiện tại, normalize sau):

```sql
CREATE TABLE travel_insurance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  issued_date DATE NOT NULL,
  insured_name TEXT NOT NULL,
  insured_dob DATE,
  insured_id_number TEXT,
  payment_date DATE,
  trip_start DATE NOT NULL,
  trip_end DATE NOT NULL,
  destination TEXT,
  scope TEXT,
  plan TEXT,
  premium REAL,
  buyer_name TEXT,
  source_email_id TEXT,         -- track xuất xứ
  source_attachment TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(insured_id_number, trip_start, destination)
);

CREATE TABLE motorbike_insurance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  issued_date DATE NOT NULL,
  plate_number TEXT NOT NULL,
  frame_number TEXT,
  engine_number TEXT,
  customer_name TEXT,
  premium_tnds REAL,
  premium_accident REAL,
  years INT,
  total_premium REAL,
  start_date DATE,
  end_date DATE,
  vehicle_type TEXT,
  brand TEXT,
  source_email_id TEXT,
  source_attachment TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(plate_number, issued_date)
);

-- ... 1 table cho mỗi sản phẩm
```

Pattern chung: lưu thêm `source_email_id`, `source_attachment`, `created_at` để truy ngược.

---

## 6. Migration plan (Excel → DB)

1. Script `tools/migrate_excel_to_sqlite.py` đọc từng sheet, parse, insert.
2. Một lần duy nhất khi cutover.
3. Sau cutover: pipeline ghi vào DB **trước**, rồi export Excel hàng ngày (snapshot).
