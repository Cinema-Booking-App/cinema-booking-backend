# HƯỚNG DẪN TÍCH HỢP THANH TOÁN VNPAY - CINEMA BOOKING SYSTEM

## BƯỚC 0: CHUẨN BỊ

### 1. Đăng ký tài khoản test trên sandbox
- Truy cập: `https://sandbox.vnpayment.vn/devreg`
- Hoàn thành thông tin đăng ký theo hướng dẫn
- Kiểm tra email để nhận thông tin tài khoản

### 2. Lấy thông tin cấu hình
Từ email xác nhận VNPay, bạn sẽ nhận được:
- `vnp_TmnCode`: Mã định danh merchant
- `vnp_HashSecret`: Khóa bí mật tạo chữ ký bảo mật

---

## BƯỚC 1: CẤU HÌNH FILE .ENV

Thêm các cấu hình sau vào file `.env` của dự án:

```env
# VNPay Configuration
VNPAY_TMN_CODE=your_tmn_code_here
VNPAY_HASH_SECRET_KEY=your_secret_key_here
VNPAY_PAYMENT_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:3000/payment/return
```

**Lưu ý:** Thay `your_tmn_code_here` và `your_secret_key_here` bằng thông tin thực tế từ VNPay.

---

## BƯỚC 2: CẤU TRÚC FILE VÀ SCHEMAS

### 2.1. Payment Schemas (`app/schemas/payments.py`)
```python
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    VNPAY = "vnpay"
    CASH = "cash"

class PaymentRequest(BaseModel):
    """Yêu cầu thanh toán"""
    order_id: str           # Mã đơn hàng (unique)
    amount: int            # Số tiền VND
    order_desc: str        # Mô tả đơn hàng
    bank_code: Optional[str] = None  # Mã ngân hàng (optional)
    language: str = "vn"   # Ngôn ngữ (vn/en)

class PaymentResponse(BaseModel):
    """Phản hồi thanh toán"""
    payment_url: str       # URL thanh toán VNPay
    order_id: str         # Mã đơn hàng

class PaymentResult(BaseModel):
    """Kết quả thanh toán"""
    success: bool
    order_id: str
    transaction_id: Optional[str] = None
    amount: Optional[int] = None
    message: str
    payment_method: PaymentMethod
    payment_status: PaymentStatus
```

---

## BƯỚC 3: API ENDPOINTS

### 3.1. Endpoint tạo thanh toán (`app/api/v1/payments.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.payments_service import PaymentService
from app.schemas.payments import PaymentRequest, PaymentResponse

router = APIRouter()
payment_service = PaymentService()

@router.post("/vnpay/create-payment", response_model=PaymentResponse)
async def create_vnpay_payment(
    payment_request: PaymentRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Tạo URL thanh toán VNPay
    
    Body request:
    {
        "order_id": "ORDER123456",
        "amount": 100000,
        "order_desc": "Thanh toán vé xem phim",
        "bank_code": "NCB",  // Optional
        "language": "vn"
    }
    """
    try:
        # Lấy IP client
        client_ip = request.client.host
        
        # Tạo bản ghi thanh toán trong DB
        payment_service.create_payment_record(
            db=db,
            order_id=payment_request.order_id,
            amount=payment_request.amount,
            payment_method="vnpay",
            order_desc=payment_request.order_desc,
            client_ip=client_ip
        )
        
        # Tạo URL thanh toán VNPay
        payment_response = payment_service.create_vnpay_payment_url(
            payment_request, client_ip
        )
        
        return payment_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )
```

### 3.2. Endpoint xử lý callback từ VNPay

```python
@router.get("/vnpay/return")
async def vnpay_return_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Callback khi user quay về từ VNPay"""
    try:
        # Lấy query parameters từ VNPay
        query_params = dict(request.query_params)
        
        # Xử lý callback
        payment_result = payment_service.handle_vnpay_callback(query_params)
        
        # Cập nhật status trong DB
        payment_service.update_payment_status(
            db, payment_result.order_id, payment_result
        )
        
        return payment_result
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/vnpay/ipn")
async def vnpay_ipn_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """IPN callback từ VNPay server"""
    try:
        query_params = dict(request.query_params)
        
        payment_result = payment_service.handle_vnpay_callback(query_params)
        payment_service.update_payment_status(
            db, payment_result.order_id, payment_result
        )
        
        # Trả về response cho VNPay
        if payment_result.success:
            return JSONResponse(
                content={'RspCode': '00', 'Message': 'success'},
                status_code=200
            )
        else:
            return JSONResponse(
                content={'RspCode': '99', 'Message': 'Unknow error'},
                status_code=200
            )
            
    except Exception as e:
        return JSONResponse(
            content={'RspCode': '99', 'Message': 'Unknow error'},
            status_code=200
        )
```

---

## BƯỚC 4: PAYMENT SERVICE

### 4.1. Service xử lý logic (`app/services/payments_service.py`)

```python
from app.core.config import settings
from app.payments.vnpay import VNPay
from app.schemas.payments import PaymentRequest, PaymentResponse

class PaymentService:
    """Service xử lý thanh toán"""
    
    def __init__(self):
        self.vnpay = VNPay()
    
    def create_vnpay_payment_url(
        self, 
        payment_request: PaymentRequest, 
        client_ip: str
    ) -> PaymentResponse:
        """Tạo URL thanh toán VNPay"""
        try:
            # Chuẩn bị dữ liệu cho VNPay
            self.vnpay.set_request_data(
                vnp_Version='2.1.0',
                vnp_Command='pay',
                vnp_TmnCode=settings.VNPAY_TMN_CODE,
                vnp_Amount=payment_request.amount * 100,  # VNPay * 100
                vnp_CurrCode='VND',
                vnp_TxnRef=payment_request.order_id,
                vnp_OrderInfo=payment_request.order_desc,
                vnp_OrderType='other',
                vnp_Locale=payment_request.language,
                vnp_CreateDate=datetime.now().strftime('%Y%m%d%H%M%S'),
                vnp_IpAddr=client_ip,
                vnp_ReturnUrl=settings.VNPAY_RETURN_URL
            )
            
            # Thêm bank code nếu có
            if payment_request.bank_code:
                self.vnpay.set_request_data(vnp_BankCode=payment_request.bank_code)
            
            # Tạo URL thanh toán
            payment_url = self.vnpay.get_payment_url(
                settings.VNPAY_PAYMENT_URL,
                settings.VNPAY_HASH_SECRET_KEY
            )
            
            return PaymentResponse(
                payment_url=payment_url,
                order_id=payment_request.order_id
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to create payment URL: {str(e)}"
            )
    
    def handle_vnpay_callback(self, callback_data: Dict[str, Any]) -> PaymentResult:
        """Xử lý callback từ VNPay"""
        # Validate signature
        self.vnpay.set_response_data(callback_data)
        is_valid = self.vnpay.validate_response(settings.VNPAY_HASH_SECRET_KEY)
        
        if not is_valid:
            return PaymentResult(
                success=False,
                order_id=callback_data.get('vnp_TxnRef', ''),
                message="Invalid signature",
                payment_method=PaymentMethod.VNPAY,
                payment_status=PaymentStatus.FAILED
            )
        
        # Xử lý kết quả
        response_code = callback_data.get('vnp_ResponseCode')
        if response_code == '00':
            status = PaymentStatus.SUCCESS
            message = "Payment successful"
            success = True
        else:
            status = PaymentStatus.FAILED
            message = f"Payment failed with code: {response_code}"
            success = False
        
        return PaymentResult(
            success=success,
            order_id=callback_data.get('vnp_TxnRef'),
            transaction_id=callback_data.get('vnp_TransactionNo'),
            amount=int(callback_data.get('vnp_Amount', 0)) // 100,
            message=message,
            payment_method=PaymentMethod.VNPAY,
            payment_status=status
        )
```

---

## BƯỚC 5: TESTING

### 5.1. Test tạo thanh toán
```bash
curl -X POST "http://localhost:8000/api/v1/payments/vnpay/create-payment" \
-H "Content-Type: application/json" \
-d '{
    "order_id": "ORDER123456",
    "amount": 100000,
    "order_desc": "Thanh toán vé xem phim Avengers",
    "language": "vn"
}'
```

### 5.2. Response mẫu
```json
{
    "payment_url": "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_Amount=10000000&vnp_Command=pay&...",
    "order_id": "ORDER123456"
}
```

### 5.3. Test cases quan trọng
- ✅ Tạo thanh toán thành công
- ✅ Xử lý callback return
- ✅ Xử lý callback IPN
- ✅ Validate signature
- ✅ Xử lý lỗi payment failed

---

## BƯỚC 6: PRODUCTION CHECKLIST

### 6.1. Thay đổi URL production
```env
VNPAY_PAYMENT_URL=https://vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=https://your-domain.com/payment/return
```

### 6.2. Security checklist
- ✅ Validate signature cho mọi callback
- ✅ Lưu trữ secret key an toàn
- ✅ Log tất cả transaction
- ✅ Implement timeout cho request
- ✅ Rate limiting cho API endpoints

### 6.3. Monitoring
- Transaction logs
- Payment success rate
- Response time monitoring
- Error rate tracking

---

## PHỤ LỤC: MÃ RESPONSE CODE VNPAY

| Code | Ý nghĩa |
|------|---------|
| 00   | Giao dịch thành công |
| 07   | Trừ tiền thành công, giao dịch bị nghi ngờ |
| 09   | Giao dịch không thành công do thẻ chưa đăng ký |
| 10   | Giao dịch không thành công do nhập sai OTP |
| 11   | Giao dịch không thành công do hết hạn chờ thanh toán |
| 12   | Giao dịch không thành công do thẻ bị khóa |
| 24   | Giao dịch không thành công do khách hàng hủy |

**Tài liệu đầy đủ:** https://sandbox.vnpayment.vn/apis/docs/huong-dan-tich-hop/