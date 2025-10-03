# Hướng Dẫn Thiết Lập Sơ Đồ Ghế Rạp Chiếu Phim

## 1. Thiết lập Loại Ghế (Seat Types)

### Thêm Loại Ghế Mới
1. Vào menu **Quản lý Loại Ghế**
2. Click **Thêm Loại Ghế Mới**
3. Thêm các loại ghế cơ bản:

| Tên      | Hệ số giá | Phụ phí     | Ghi chú                    |
|----------|:---------:|------------:|----------------------------|
| Standard |   1.00    | 0đ          | Ghế thường                 |
| VIP      |   1.50    | 50,000đ     | Ghế VIP với đệm mềm        |
| Couple   |   2.00    | 100,000đ    | Ghế đôi dành cho 2 người   |

## 2. Tạo Layout Phòng Chiếu

### Tạo Layout Mới
1. Vào menu **Quản lý Layout**
2. Click **Tạo Layout Mới**

#### Ví dụ:
- **Layout Phòng Thường:**
  - Tên: "Standard 10x15"
  - Số hàng: 10
  - Số cột: 15
  - Vị trí màn hình: "front"
  - Lối đi: cột 7-8
- **Layout Phòng VIP:**
  - Tên: "VIP 8x12"
  - Số hàng: 8
  - Số cột: 12
  - Vị trí màn hình: "front"
  - Lối đi: cột 6

## 3. Thiết lập Phòng Chiếu

1. Vào menu **Quản lý Phòng Chiếu**
2. Click **Thêm Phòng Chiếu Mới**

#### Ví dụ:
- **Phòng Standard:**
  - Tên phòng: "Phòng 1"
  - Rạp: Chọn rạp từ danh sách
  - Loại phòng: Standard
  - Layout: "Standard 10x15"
  - Tổng số ghế: 150
- **Phòng VIP:**
  - Tên phòng: "Phòng VIP"
  - Rạp: Chọn rạp từ danh sách
  - Loại phòng: VIP
  - Layout: "VIP 8x12"
  - Tổng số ghế: 96

## 4. Tạo Sơ Đồ Ghế

1. Vào menu **Quản lý Sơ Đồ Ghế**
2. Chọn phòng cần tạo sơ đồ
3. Click **Tạo Sơ Đồ Ghế Tự Động**
4. Tùy chỉnh loại ghế:
   - Chọn vùng ghế cần đặt loại
   - Chọn loại ghế (VIP, Standard, Couple)
   - Ví dụ:
     - Hàng A-C: Ghế Standard
     - Hàng D-F: Ghế VIP
     - Hàng G-H: Ghế Couple
5. Đánh dấu ghế đặc biệt:
   - Chọn ghế cạnh lối đi
   - Đánh dấu "Edge Seat"
6. Lưu cấu hình

## 5. Kiểm tra và Xác nhận

1. Xem trước sơ đồ
   - Kiểm tra vị trí các loại ghế
   - Kiểm tra lối đi
   - Kiểm tra đánh số ghế
2. Kích hoạt sơ đồ
   - Click **Kích hoạt Sơ đồ**
   - Xác nhận kích hoạt

---

> **Lưu ý quan trọng:**
>
> - **Đặt tên ghế:**
>   - Hàng được đánh theo chữ cái (A, B, C...)
>   - Số ghế đánh từ trái sang phải (1, 2, 3...)
>   - Ví dụ:
>
>     ```
>     A1, A2, B1, B2, ...
>     ```
>
> - **Lối đi:**
>   - Nên đặt lối đi ở giữa để thuận tiện
>   - Đánh dấu rõ ghế cạnh lối đi
>
> - **Loại ghế:**
>   - Ghế VIP thường đặt ở giữa, vị trí đẹp
>   - Ghế Couple thường đặt phía sau
>   - Ghế Standard phân bố đều các vị trí còn lại