# 🎬 KIẾN TRÚC HỆ THỐNG REALTIME - CINEMA BOOKING

## 📋 Tổng quan

Hệ thống đặt vé xem phim sử dụng WebSocket để cập nhật trạng thái ghế ngồi theo thời gian thực, đảm bảo nhiều người dùng có thể thấy được trạng thái ghế mới nhất khi có thay đổi.

## 🏗️ Kiến trúc hệ thống

```
Frontend (Client)
    ↕️ WebSocket Connection  
WebSocket API Layer (/api/v1/websocket.py)
    ↕️ Manager Integration
WebSocket Manager (/core/websocket_manager.py)
    ↕️ Service Layer Calls
Business Logic (/services/reservations_service.py)
    ↕️ Database Operations
PostgreSQL Database
    ↕️ Background Tasks
Cleanup Service (/core/background_tasks.py)
```

## 🔧 Các thành phần chính

### 1. **WebSocket Manager** (`/core/websocket_manager.py`)
- **Chức năng**: Quản lý tất cả kết nối WebSocket
- **Trách nhiệm**:
  - Nhóm client theo suất chiếu (showtime_id)
  - Gửi thông báo broadcast cho tất cả client trong cùng nhóm
  - Quản lý kết nối/ngắt kết nối
  - Xử lý tin nhắn ping/pong

**Các phương thức chính**:
- `connect()`: Kết nối client vào nhóm suất chiếu
- `disconnect()`: Ngắt kết nối và dọn dẹp
- `send_seat_reserved()`: Thông báo ghế đã được đặt
- `send_seat_released()`: Thông báo ghế đã được giải phóng
- `broadcast_to_showtime()`: Gửi tin nhắn đến tất cả client

### 2. **WebSocket API** (`/api/v1/websocket.py`)
- **Chức năng**: Endpoint WebSocket cho client kết nối
- **Trách nhiệm**:
  - Xử lý kết nối WebSocket từ client
  - Gửi dữ liệu ban đầu khi client kết nối
  - Lắng nghe tin nhắn ping/pong từ client
  - Xử lý lỗi kết nối

**Endpoint chính**:
- `ws://localhost:8000/api/v1/ws/seats/{showtime_id}?session_id={session_id}`

### 3. **Reservation Service** (`/services/reservations_service.py`)
- **Chức năng**: Xử lý logic nghiệp vụ đặt ghế
- **Tích hợp WebSocket**:
  - Gửi thông báo khi đặt ghế thành công
  - Gửi thông báo khi hủy ghế
  - Gửi thông báo khi ghế hết hạn

### 4. **Background Tasks** (`/core/background_tasks.py`)
- **Chức năng**: Tác vụ chạy nền
- **Trách nhiệm**:
  - Dọn dẹp ghế hết hạn mỗi 30 giây
  - Tự động gửi thông báo WebSocket khi giải phóng ghế

### 5. **WebSocket Schemas** (`/schemas/websocket.py`)
- **Chức năng**: Định nghĩa cấu trúc dữ liệu
- **Các schema chính**:
  - `WebSocketMessage`: Tin nhắn cơ bản
  - `SeatUpdateData`: Cập nhật trạng thái ghế
  - `SeatsReservedData`: Thông báo ghế đã đặt
  - `SeatsReleasedData`: Thông báo ghế giải phóng

## 🔄 Luồng hoạt động

### **Luồng đặt ghế**:
1. User A đặt ghế → API `/reservations/multiple`
2. Service lưu vào database
3. Service gọi `websocket_manager.send_seat_reserved()`
4. WebSocket Manager broadcast đến tất cả client khác
5. User B, C, D nhận thông báo ghế đã được đặt

### **Luồng giải phóng ghế**:
1. User hủy ghế hoặc ghế hết hạn
2. Service xóa khỏi database  
3. Service gọi `websocket_manager.send_seat_released()`
4. Tất cả client nhận thông báo ghế available

### **Luồng kết nối client**:
1. Client mở WebSocket connection
2. WebSocket API gửi `initial_data` (danh sách ghế đã đặt)
3. Client lắng nghe các event: `seats_reserved`, `seats_released`
4. Client cập nhật UI theo thời gian thực

## 📨 Các loại tin nhắn WebSocket

### **1. Initial Data** (Server → Client)
```json
{
  "type": "initial_data",
  "showtime_id": 1,
  "data": {
    "reserved_seats": [
      {
        "seat_id": 15,
        "status": "pending",
        "expires_at": "2024-01-01T10:30:00Z",
        "user_session": "session_abc123"
      }
    ]
  }
}
```

### **2. Seats Reserved** (Server → All Clients)
```json
{
  "type": "seats_reserved",
  "showtime_id": 1,
  "data": {
    "seat_ids": [15, 16],
    "user_session": "session_xyz789",
    "timestamp": "2024-01-01T10:25:30Z"
  }
}
```

### **3. Seats Released** (Server → All Clients)
```json
{
  "type": "seats_released",
  "showtime_id": 1,
  "data": {
    "seat_ids": [15, 16],
    "timestamp": "2024-01-01T10:35:30Z"
  }
}
```

### **4. Ping/Pong** (Bidirectional)
```json
// Client → Server
{"type": "ping"}

// Server → Client  
{"type": "pong"}
```

## ⚡ Tối ưu hóa hiệu suất

### **1. Connection Pooling**
- Nhóm client theo `showtime_id`
- Chỉ gửi thông báo cho client liên quan

### **2. Non-blocking Operations**
- Sử dụng `asyncio.create_task()` để gửi WebSocket không chặn API
- Không làm thất bại đặt ghế nếu WebSocket lỗi

### **3. Background Cleanup**
- Tự động dọn dẹp ghế hết hạn mỗi 30 giây
- Gửi thông báo realtime khi giải phóng

### **4. Error Handling**
- Graceful disconnect khi client mất kết nối
- Retry mechanism cho WebSocket failures
- Fallback mechanism trong file test

## 🧪 Testing

### **File test**: `websocket_test.html`
- Giao diện trực quan 5x10 ghế (50 ghế)
- Hỗ trợ nhiều user cùng lúc
- Simulation mode khi API không khả dụng
- Realtime updates với màu sắc phân biệt

### **Cách test**:
1. Mở nhiều tab browser với file test
2. Kết nối WebSocket với tên user khác nhau
3. Chọn ghế ở tab 1 → Tab 2 thấy ghế đang được chọn
4. Xác nhận đặt ghế → Tất cả tab thấy ghế đã được đặt

## 🔐 Bảo mật

### **CORS Configuration**
- Chặn cross-origin requests từ domain không được phép
- Cho phép localhost ports cho development

### **Session Management**  
- Mỗi client có `session_id` riêng
- Validate quyền hủy ghế (chỉ người đặt mới hủy được)

## 📊 Monitoring & Logging

### **WebSocket Connections**
- Endpoint `/ws/status/{showtime_id}` để check active connections
- Log connect/disconnect events

### **Performance Metrics**
- Số tin nhắn gửi thành công/thất bại
- Thời gian response WebSocket
- Số client active theo thời gian

## 🚀 Deployment

### **Production Considerations**:
1. **Load Balancing**: Sticky sessions cho WebSocket
2. **Scaling**: Redis pub/sub cho multiple server instances  
3. **Monitoring**: WebSocket connection metrics
4. **Error Tracking**: Detailed logging cho WebSocket failures

---

## 📚 Tài liệu tham khảo

- **WebSocket Manager**: `/core/websocket_manager.py`
- **API Endpoints**: `/api/v1/websocket.py` 
- **Business Logic**: `/services/reservations_service.py`
- **Background Tasks**: `/core/background_tasks.py`
- **Test Interface**: `/websocket_test.html`

---

**Lưu ý**: Hệ thống này đảm bảo tính realtime cao, user experience mượt mà và khả năng scale tốt cho ứng dụng đặt vé xem phim.