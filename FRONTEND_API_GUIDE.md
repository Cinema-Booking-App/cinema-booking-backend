# 🚀 HƯỚNG DẪN SỬ DỤNG API CHO FRONTEND

## 📋 Tổng quan API

Hệ thống cung cấp **2 loại API chính**:
1. **HTTP REST API**: Cho các thao tác CRUD (Create, Read, Update, Delete)
2. **WebSocket API**: Cho cập nhật realtime (seat booking status)

**Base URL**: `http://localhost:8000/api/v1`

---

## 🌐 HTTP REST API

### **1. API Đặt ghế (Reservations)**

#### **📌 Lấy danh sách ghế đã đặt**
```javascript
// GET /api/v1/reservations/{showtime_id}
const getReservedSeats = async (showtimeId) => {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/reservations/${showtimeId}`);
    const data = await response.json();
    
    if (data.success) {
      return data.data; // Array of reserved seats
    }
  } catch (error) {
    console.error('Error fetching reserved seats:', error);
  }
};

// Response example:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "seat_id": 15,
      "showtime_id": 1,
      "session_id": "session_abc123",
      "status": "pending",
      "expires_at": "2024-01-01T10:30:00Z",
      "created_at": "2024-01-01T10:25:00Z"
    }
  ]
}
```

#### **📌 Đặt một ghế**
```javascript
// POST /api/v1/reservations
const reserveSingleSeat = async (seatData) => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/reservations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        seat_id: seatData.seatId,
        showtime_id: seatData.showtimeId,
        session_id: seatData.sessionId,
        status: 'pending'
      })
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error reserving seat:', error);
  }
};
```

#### **📌 Đặt nhiều ghế cùng lúc (Realtime)**
```javascript
// POST /api/v1/reservations/multiple
const reserveMultipleSeats = async (seatsData) => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/reservations/multiple', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(seatsData.map(seat => ({
        seat_id: seat.seatId,
        showtime_id: seat.showtimeId,
        session_id: seat.sessionId,
        status: 'pending'
      })))
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error reserving multiple seats:', error);
  }
};

// Usage example:
const seatsToReserve = [
  { seatId: 15, showtimeId: 1, sessionId: 'user_session_123' },
  { seatId: 16, showtimeId: 1, sessionId: 'user_session_123' }
];
await reserveMultipleSeats(seatsToReserve);
```

#### **📌 Hủy đặt ghế**
```javascript
// DELETE /api/v1/reservations/{showtime_id}?seat_ids=15,16&session_id=user_session_123
const cancelReservations = async (showtimeId, seatIds, sessionId) => {
  try {
    const seatIdsStr = seatIds.join(',');
    const response = await fetch(
      `http://localhost:8000/api/v1/reservations/${showtimeId}?seat_ids=${seatIdsStr}&session_id=${sessionId}`,
      {
        method: 'DELETE',
      }
    );
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error cancelling reservations:', error);
  }
};

// Usage:
await cancelReservations(1, [15, 16], 'user_session_123');
```

### **2. API WebSocket Status**

#### **📌 Kiểm tra trạng thái kết nối WebSocket**
```javascript
// GET /api/v1/ws/status/{showtime_id}
const getWebSocketStatus = async (showtimeId) => {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/ws/status/${showtimeId}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting WebSocket status:', error);
  }
};

// Response:
{
  "showtime_id": 1,
  "active_connections": 5,
  "status": "active"
}
```

---

## ⚡ WebSocket API (Realtime)

### **1. Kết nối WebSocket**

```javascript
class SeatBookingWebSocket {
  constructor(showtimeId, sessionId, userName) {
    this.showtimeId = showtimeId;
    this.sessionId = sessionId;
    this.userName = userName;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    const wsUrl = `ws://localhost:8000/api/v1/ws/seats/${this.showtimeId}?session_id=${this.sessionId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = (event) => {
      console.log('🟢 WebSocket connected');
      this.reconnectAttempts = 0;
      this.onConnected(event);
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      console.log('🔴 WebSocket disconnected');
      this.onDisconnected(event);
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      this.onError(error);
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'initial_data':
        this.onInitialData(message.data);
        break;
      case 'seats_reserved':
        this.onSeatsReserved(message.data);
        break;
      case 'seats_released':
        this.onSeatsReleased(message.data);
        break;
      case 'seat_update':
        this.onSeatUpdate(message.data);
        break;
      case 'pong':
        console.log('🏓 Pong received');
        break;
      default:
        console.log('❓ Unknown message type:', message.type);
    }
  }

  // Send ping to keep connection alive
  sendPing() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping' }));
    }
  }

  // Send heartbeat
  sendHeartbeat() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'heartbeat' }));
    }
  }

  // Reconnect logic
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => {
        this.connect();
      }, 2000 * this.reconnectAttempts); // Exponential backoff
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
    }
  }

  // Override these methods in your implementation
  onConnected(event) { /* Override this */ }
  onDisconnected(event) { /* Override this */ }
  onError(error) { /* Override this */ }
  onInitialData(data) { /* Override this */ }
  onSeatsReserved(data) { /* Override this */ }
  onSeatsReleased(data) { /* Override this */ }
  onSeatUpdate(data) { /* Override this */ }
}
```

### **2. Sử dụng WebSocket trong React/Vue/Angular**

#### **React Example:**
```jsx
import React, { useState, useEffect, useRef } from 'react';

const SeatBookingComponent = ({ showtimeId, sessionId, userName }) => {
  const [seats, setSeats] = useState({});
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [selectedSeats, setSelectedSeats] = useState(new Set());
  const wsRef = useRef(null);

  useEffect(() => {
    // Initialize WebSocket
    wsRef.current = new SeatBookingWebSocket(showtimeId, sessionId, userName);
    
    // Override WebSocket event handlers
    wsRef.current.onConnected = () => {
      setConnectionStatus('connected');
    };

    wsRef.current.onDisconnected = () => {
      setConnectionStatus('disconnected');
    };

    wsRef.current.onInitialData = (data) => {
      const seatMap = {};
      // Initialize all seats as available
      for (let i = 1; i <= 50; i++) {
        seatMap[i] = { status: 'available', userSession: null };
      }
      
      // Mark reserved seats
      data.reserved_seats.forEach(seat => {
        seatMap[seat.seat_id] = {
          status: seat.status,
          userSession: seat.user_session,
          expiresAt: seat.expires_at
        };
      });
      
      setSeats(seatMap);
    };

    wsRef.current.onSeatsReserved = (data) => {
      setSeats(prevSeats => {
        const newSeats = { ...prevSeats };
        data.seat_ids.forEach(seatId => {
          newSeats[seatId] = {
            status: 'reserved',
            userSession: data.user_session,
            timestamp: data.timestamp
          };
        });
        return newSeats;
      });

      // Remove from selected if it was ours
      if (data.user_session === sessionId) {
        setSelectedSeats(prev => {
          const newSelected = new Set(prev);
          data.seat_ids.forEach(seatId => newSelected.delete(seatId));
          return newSelected;
        });
      }
    };

    wsRef.current.onSeatsReleased = (data) => {
      setSeats(prevSeats => {
        const newSeats = { ...prevSeats };
        data.seat_ids.forEach(seatId => {
          newSeats[seatId] = {
            status: 'available',
            userSession: null,
            timestamp: data.timestamp
          };
        });
        return newSeats;
      });
    };

    // Connect
    wsRef.current.connect();

    // Setup ping interval
    const pingInterval = setInterval(() => {
      wsRef.current.sendPing();
    }, 30000); // Every 30 seconds

    // Cleanup
    return () => {
      clearInterval(pingInterval);
      wsRef.current.disconnect();
    };
  }, [showtimeId, sessionId, userName]);

  const toggleSeatSelection = (seatId) => {
    if (seats[seatId]?.status === 'reserved') {
      alert('Ghế này đã được đặt!');
      return;
    }

    setSelectedSeats(prev => {
      const newSelected = new Set(prev);
      if (newSelected.has(seatId)) {
        newSelected.delete(seatId);
      } else {
        newSelected.add(seatId);
      }
      return newSelected;
    });
  };

  const confirmBooking = async () => {
    if (selectedSeats.size === 0) {
      alert('Vui lòng chọn ít nhất một ghế');
      return;
    }

    const seatsToBook = Array.from(selectedSeats).map(seatId => ({
      seatId,
      showtimeId,
      sessionId
    }));

    try {
      await reserveMultipleSeats(seatsToBook);
      alert('Đặt ghế thành công!');
    } catch (error) {
      alert('Lỗi khi đặt ghế: ' + error.message);
    }
  };

  return (
    <div className="seat-booking">
      <div className="connection-status">
        Status: {connectionStatus === 'connected' ? '🟢 Connected' : '🔴 Disconnected'}
      </div>
      
      <div className="seat-grid">
        {Array.from({ length: 50 }, (_, i) => i + 1).map(seatId => {
          const seat = seats[seatId] || { status: 'available' };
          const isSelected = selectedSeats.has(seatId);
          
          return (
            <div
              key={seatId}
              className={`seat ${seat.status} ${isSelected ? 'selected' : ''}`}
              onClick={() => toggleSeatSelection(seatId)}
            >
              {seatId}
            </div>
          );
        })}
      </div>

      <div className="booking-controls">
        <div>Đã chọn: {Array.from(selectedSeats).join(', ') || 'Chưa chọn ghế nào'}</div>
        <button onClick={confirmBooking} disabled={selectedSeats.size === 0}>
          Xác nhận đặt ghế
        </button>
      </div>
    </div>
  );
};

export default SeatBookingComponent;
```

#### **Vue 3 Example:**
```vue
<template>
  <div class="seat-booking">
    <div class="connection-status">
      Status: {{ connectionStatus === 'connected' ? '🟢 Connected' : '🔴 Disconnected' }}
    </div>
    
    <div class="seat-grid">
      <div
        v-for="seatId in 50"
        :key="seatId"
        :class="getSeatClass(seatId)"
        @click="toggleSeatSelection(seatId)"
      >
        {{ seatId }}
      </div>
    </div>

    <div class="booking-controls">
      <div>Đã chọn: {{ selectedSeatsArray.join(', ') || 'Chưa chọn ghế nào' }}</div>
      <button @click="confirmBooking" :disabled="selectedSeats.size === 0">
        Xác nhận đặt ghế
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';

export default {
  name: 'SeatBookingComponent',
  props: {
    showtimeId: Number,
    sessionId: String,
    userName: String
  },
  setup(props) {
    const seats = ref({});
    const connectionStatus = ref('disconnected');
    const selectedSeats = ref(new Set());
    let wsConnection = null;
    let pingInterval = null;

    const selectedSeatsArray = computed(() => Array.from(selectedSeats.value));

    const getSeatClass = (seatId) => {
      const seat = seats.value[seatId] || { status: 'available' };
      const isSelected = selectedSeats.value.has(seatId);
      return `seat ${seat.status} ${isSelected ? 'selected' : ''}`;
    };

    const toggleSeatSelection = (seatId) => {
      const seat = seats.value[seatId];
      if (seat?.status === 'reserved') {
        alert('Ghế này đã được đặt!');
        return;
      }

      if (selectedSeats.value.has(seatId)) {
        selectedSeats.value.delete(seatId);
      } else {
        selectedSeats.value.add(seatId);
      }
    };

    const confirmBooking = async () => {
      if (selectedSeats.value.size === 0) {
        alert('Vui lòng chọn ít nhất một ghế');
        return;
      }

      const seatsToBook = Array.from(selectedSeats.value).map(seatId => ({
        seatId,
        showtimeId: props.showtimeId,
        sessionId: props.sessionId
      }));

      try {
        await reserveMultipleSeats(seatsToBook);
        alert('Đặt ghế thành công!');
      } catch (error) {
        alert('Lỗi khi đặt ghế: ' + error.message);
      }
    };

    onMounted(() => {
      // WebSocket setup
      wsConnection = new SeatBookingWebSocket(props.showtimeId, props.sessionId, props.userName);
      
      wsConnection.onConnected = () => {
        connectionStatus.value = 'connected';
      };

      wsConnection.onDisconnected = () => {
        connectionStatus.value = 'disconnected';
      };

      wsConnection.onInitialData = (data) => {
        const seatMap = {};
        for (let i = 1; i <= 50; i++) {
          seatMap[i] = { status: 'available', userSession: null };
        }
        
        data.reserved_seats.forEach(seat => {
          seatMap[seat.seat_id] = {
            status: seat.status,
            userSession: seat.user_session,
            expiresAt: seat.expires_at
          };
        });
        
        seats.value = seatMap;
      };

      wsConnection.onSeatsReserved = (data) => {
        data.seat_ids.forEach(seatId => {
          seats.value[seatId] = {
            status: 'reserved',
            userSession: data.user_session,
            timestamp: data.timestamp
          };
        });

        if (data.user_session === props.sessionId) {
          data.seat_ids.forEach(seatId => selectedSeats.value.delete(seatId));
        }
      };

      wsConnection.onSeatsReleased = (data) => {
        data.seat_ids.forEach(seatId => {
          seats.value[seatId] = {
            status: 'available',
            userSession: null,
            timestamp: data.timestamp
          };
        });
      };

      wsConnection.connect();
      
      pingInterval = setInterval(() => {
        wsConnection.sendPing();
      }, 30000);
    });

    onUnmounted(() => {
      if (pingInterval) clearInterval(pingInterval);
      if (wsConnection) wsConnection.disconnect();
    });

    return {
      seats,
      connectionStatus,
      selectedSeats,
      selectedSeatsArray,
      getSeatClass,
      toggleSeatSelection,
      confirmBooking
    };
  }
};
</script>
```

---

## 🎨 CSS Styles cho Seat Grid

```css
.seat-booking {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.connection-status {
  text-align: center;
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 4px;
  background: #f8f9fa;
}

.seat-grid {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 8px;
  max-width: 500px;
  margin: 20px auto;
}

.seat {
  width: 40px;
  height: 40px;
  border: 2px solid #ddd;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  transition: all 0.3s ease;
}

.seat.available {
  background: #e8f5e8;
  border-color: #28a745;
  color: #28a745;
}

.seat.available:hover {
  background: #d4edda;
  transform: scale(1.1);
}

.seat.reserved {
  background: #f8d7da;
  border-color: #dc3545;
  color: #721c24;
  cursor: not-allowed;
}

.seat.selected {
  background: #d1ecf1;
  border-color: #17a2b8;
  color: #0c5460;
  transform: scale(1.1);
}

.booking-controls {
  text-align: center;
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
}

.booking-controls button {
  padding: 10px 20px;
  margin-top: 10px;
  border: none;
  border-radius: 4px;
  background: #007bff;
  color: white;
  cursor: pointer;
  font-weight: bold;
}

.booking-controls button:hover {
  background: #0056b3;
}

.booking-controls button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}
```

---

## 🔧 Utility Functions

```javascript
// API utility functions
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Generate unique session ID
const generateSessionId = () => {
  return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
};

// Format seat numbers for display
const formatSeatNumbers = (seatIds) => {
  return seatIds.sort((a, b) => a - b).join(', ');
};

// Check if seat is available for booking
const isSeatAvailable = (seat) => {
  return !seat || seat.status === 'available';
};

// Get seat row and column from seat ID (assuming 10 seats per row)
const getSeatPosition = (seatId) => {
  const row = Math.ceil(seatId / 10);
  const col = ((seatId - 1) % 10) + 1;
  return { row, col };
};

// Format seat position for display (e.g., "A5", "B10")
const formatSeatPosition = (seatId) => {
  const { row, col } = getSeatPosition(seatId);
  const rowLetter = String.fromCharCode(65 + row - 1); // A, B, C...
  return `${rowLetter}${col}`;
};

// Validate seat selection (max 8 seats per booking)
const validateSeatSelection = (selectedSeats) => {
  if (selectedSeats.size === 0) {
    return { valid: false, message: 'Vui lòng chọn ít nhất một ghế' };
  }
  
  if (selectedSeats.size > 8) {
    return { valid: false, message: 'Chỉ được chọn tối đa 8 ghế mỗi lần đặt' };
  }
  
  return { valid: true };
};

// Error handling for API calls
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    console.error('API Error:', error.response.data);
    return error.response.data.message || 'Lỗi từ server';
  } else if (error.request) {
    // Network error
    console.error('Network Error:', error.request);
    return 'Lỗi kết nối mạng';
  } else {
    // Other error
    console.error('Error:', error.message);
    return error.message;
  }
};
```

---

## 📱 Mobile Responsive

```css
/* Mobile styles */
@media (max-width: 768px) {
  .seat-grid {
    grid-template-columns: repeat(5, 1fr);
    max-width: 300px;
  }
  
  .seat {
    width: 35px;
    height: 35px;
    font-size: 10px;
  }
  
  .seat-booking {
    padding: 10px;
  }
}
```

---

## 🚨 Error Handling & Best Practices

### **1. Connection Management**
```javascript
// Always handle WebSocket reconnection
const wsManager = {
  connect() {
    this.ws = new WebSocket(wsUrl);
    this.ws.onclose = () => {
      console.log('Connection lost, attempting to reconnect...');
      setTimeout(() => this.connect(), 2000);
    };
  }
};
```

### **2. API Error Handling**
```javascript
// Always handle API failures gracefully
const apiCall = async (url, options) => {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
```

### **3. Loading States**
```javascript
const [loading, setLoading] = useState(false);

const handleBooking = async () => {
  setLoading(true);
  try {
    await reserveMultipleSeats(selectedSeats);
  } catch (error) {
    // Handle error
  } finally {
    setLoading(false);
  }
};
```

---

## 🎯 Tóm tắt cho Frontend Developer

### **Bước 1**: Thiết lập HTTP API calls cho CRUD operations
### **Bước 2**: Implement WebSocket connection cho realtime updates  
### **Bước 3**: Xử lý state management cho seat selection
### **Bước 4**: Thêm error handling và reconnection logic
### **Bước 5**: Style UI với CSS responsive

**Lưu ý quan trọng**: 
- Luôn validate dữ liệu trước khi gửi API
- Xử lý network errors gracefully
- Implement loading states cho UX tốt hơn
- Test với nhiều browser tabs để đảm bảo realtime sync

🎉 **Chúc các bạn Frontend implement thành công!**