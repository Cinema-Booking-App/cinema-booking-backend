## Quy trình Đặt vé và Thanh toán trong Hệ thống Rạp chiếu phim

Quy trình đặt vé và thanh toán là trái tim của mọi hệ thống đặt vé xem phim trực tuyến. Nó bao gồm một loạt các bước liên kết chặt chẽ giữa giao diện người dùng (frontend) và hệ thống xử lý phía máy chủ (backend), đảm bảo sự liền mạch, chính xác và an toàn cho mỗi giao dịch.

---

### I. Quy trình Đặt vé (Booking Process)

Quá trình đặt vé bắt đầu từ khi người dùng muốn xem phim và kết thúc khi họ sẵn sàng thanh toán.

#### 1. Chọn Phim và Suất chiếu

* **Người dùng**: Duyệt qua danh sách phim, chọn một **bộ phim** ưng ý và sau đó là một **suất chiếu** (`showtime_id`) cụ thể (bao gồm thời gian, rạp và phòng chiếu).
* **Hệ thống**: Backend truy vấn bảng `showtimes` để hiển thị đầy đủ thông tin chi tiết về suất chiếu đã chọn, như giá vé cơ bản và định dạng phim.

#### 2. Hiển thị và Chọn Ghế

* **Người dùng**: Yêu cầu sơ đồ ghế cho suất chiếu đã chọn.
* **Hệ thống**:
    * Backend tra cứu bảng `seats` (liên kết với `rooms` và `seat_layouts`) để biết bố cục phòng chiếu.
    * Truy vấn bảng `tickets` để xác định các ghế đã **được bán** (`status = 'confirmed'`).
    * Truy vấn bảng **`seat_reservations`** để kiểm tra các ghế đang **được giữ tạm thời** (`status = 'pending'` và chưa hết hạn `expires_at`).
    * Frontend hiển thị sơ đồ ghế với trạng thái rõ ràng: **trống**, **đã bán**, hoặc **đang được giữ**.
* **Người dùng**: Chọn (click vào) một hoặc nhiều ghế mong muốn từ sơ đồ.

#### 3. Giữ Ghế Tạm thời (Realtime & Timeout)

Đây là bước cực kỳ quan trọng để ngăn chặn việc trùng lặp đặt chỗ và quản lý thời gian chờ thanh toán.

* **Người dùng**: Chọn ghế trên giao diện.
* **Hệ thống**:
    * Backend nhận yêu cầu giữ ghế (gồm `seat_ids` và `showtime_id`).
    * Kiểm tra tính hợp lệ của từng ghế: Đảm bảo ghế đó **chưa bán** và **chưa bị giữ** bởi ai khác trong cùng một suất chiếu.
    * Nếu hợp lệ, một **Transaction database** sẽ được thực hiện để:
        * Tạo bản ghi mới trong bảng **`seat_reservations`** cho mỗi ghế đã chọn.
        * Đặt `status = 'pending'` cho các bản ghi này.
        * Đặt `reserved_at = thời điểm hiện tại`.
        * Thiết lập thời gian hết hạn `expires_at = thời điểm hiện tại + 10 phút` (hoặc thời gian timeout khác bạn định cấu hình).
    * **Cập nhật Realtime**: Ngay lập tức, backend sử dụng **WebSockets** hoặc Server-Sent Events (SSE) để gửi thông báo đến **tất cả các người dùng** đang xem suất chiếu đó. Điều này giúp sơ đồ ghế của họ được cập nhật tức thì, hiển thị các ghế vừa được giữ là "đang chờ thanh toán".
    * Nếu ghế đã bị người khác chọn trước đó (Race Condition), transaction sẽ thất bại và frontend nhận được thông báo lỗi.

#### 4. Chọn Combo Bắp nước (Tùy chọn)

* **Người dùng**: Duyệt danh sách combo (`combos`) và thêm số lượng mong muốn vào đơn hàng.
* **Hệ thống**: Thông tin combo được ghi nhận tạm thời ở frontend, sẵn sàng cho bước tính toán giá.

#### 5. Áp dụng Khuyến mãi (Tùy chọn)

* **Người dùng**: Nhập mã khuyến mãi (`promotion_code`).
* **Hệ thống**: Backend kiểm tra mã này trong bảng `promotions` về tính hợp lệ, thời hạn, và số lượt sử dụng. Nếu mã hợp lệ, thông tin giảm giá sẽ được áp dụng ở bước tiếp theo. (Lưu ý: `promotion_id` thường được lưu ở bảng `transactions` nếu áp dụng cho toàn bộ đơn hàng).

#### 6. Tính toán Tổng tiền

* **Người dùng**: Yêu cầu xem tổng số tiền phải trả.
* **Hệ thống**:
    * Backend tính **tổng tiền vé** dựa trên số lượng ghế và `showtimes.ticket_price`.
    * Tính **tổng tiền combo** từ các combo đã chọn.
    * Áp dụng **giảm giá** từ mã khuyến mãi hợp lệ vào tổng số tiền.
    * Trả về `total_amount` cuối cùng cho frontend.

---

### II. Quy trình Thanh toán (Payment Process)

Sau khi xác nhận đơn hàng, người dùng tiến hành thanh toán để hoàn tất việc đặt vé.

#### 1. Khởi tạo Giao dịch

* **Người dùng**: Xác nhận đơn hàng và chọn phương thức thanh toán.
* **Hệ thống**:
    * Backend tạo một bản ghi mới trong bảng **`transactions`** với `status = 'pending'`.
    * Lưu các thông tin liên quan như `user_id`, `total_amount`, `payment_method`, và `promotion_id` (nếu có).
    * Hệ thống sẽ điều hướng người dùng đến cổng thanh toán (ví dụ: MoMo, VNPay, ZaloPay...).

#### 2. Xử lý Phản hồi từ Cổng Thanh toán (Payment Gateway Callback)

Đây là một bước **cực kỳ quan trọng** để xác nhận kết quả thanh toán.

* **Cổng Thanh toán**: Sau khi người dùng hoàn tất (hoặc hủy) thanh toán, cổng thanh toán sẽ gửi một phản hồi (callback) đến một **API Endpoint** được cấu hình sẵn trên backend của bạn. Phản hồi này chứa thông tin về kết quả giao dịch.
* **Hệ thống (Backend - Callback Endpoint)**:
    * Nhận và xác minh tính hợp lệ của phản hồi từ cổng thanh toán (để chống giả mạo).
    * **Dựa vào kết quả thanh toán**:
        * **Nếu thành công**:
            * Cập nhật `transactions.status` từ `pending` thành **`'success'`**.
            * Với mỗi ghế đã được giữ cho giao dịch này (trong `seat_reservations`), cập nhật `status` thành `'confirmed'`.
            * Tạo các bản ghi mới trong bảng **`tickets`** với `status = 'confirmed'` cho từng ghế đã mua.
            * Tạo các bản ghi liên kết trong `transaction_tickets` và `transaction_combos`.
            * (Tùy chọn) Cập nhật `promotions.used_count` để ghi nhận lượt sử dụng khuyến mãi.
            * (Tùy chọn) Gửi email/SMS xác nhận vé điện tử cho người dùng.
        * **Nếu thất bại / bị hủy**:
            * Cập nhật `transactions.status` từ `pending` thành **`'failed'`** hoặc **`'cancelled'`**.
            * Với mỗi ghế trong `seat_reservations` của giao dịch này, cập nhật `status` thành **`'cancelled'`** để giải phóng ghế.
            * **Cập nhật Realtime**: Gửi thông báo qua WebSockets để cập nhật trạng thái ghế trên sơ đồ, hiển thị các ghế đó là "trống" trở lại.
            * (Tùy chọn) Gửi email/SMS thông báo giao dịch thất bại cho người dùng.

### III. Cơ chế Giải phóng Ghế Tự động (Background Job)

* **Hệ thống (Background Job / Cron Job)**: Một tác vụ chạy định kỳ (ví dụ: mỗi phút) trên backend sẽ:
    * Tìm kiếm tất cả các bản ghi trong bảng `seat_reservations` có `status = 'pending'` và `expires_at` đã **quá thời điểm hiện tại**.
    * Với mỗi bản ghi tìm được, cập nhật `status` của nó thành `'cancelled'`.
    * **Cập nhật Realtime**: Gửi thông báo qua WebSockets để cập nhật trạng thái ghế trên sơ đồ cho tất cả người dùng, giúp các ghế này trở về trạng thái "trống" và có thể được đặt lại.

---

Bằng cách triển khai quy trình này với sự kết hợp của cơ sở dữ liệu mạnh mẽ (đặc biệt là bảng `seat_reservations`), giao dịch nguyên tử (ACID Transactions), và công nghệ realtime như WebSockets, bạn sẽ có một hệ thống đặt vé hiệu quả, đáng tin cậy và mang lại trải nghiệm tốt cho người dùng.