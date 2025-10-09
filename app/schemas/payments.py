from pydantic import BaseModel, Field
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
    order_id: str
    amount: int  # Số tiền VND
    order_desc: str
    bank_code: Optional[str] = None
    language: str = "vn"


class PaymentResponse(BaseModel):
    """Phản hồi thanh toán"""
    payment_url: str
    order_id: str


class VNPayCallback(BaseModel):
    """VNPay callback/return data"""
    vnp_Amount: str
    vnp_BankCode: str
    vnp_BankTranNo: Optional[str] = None
    vnp_CardType: str
    vnp_OrderInfo: str
    vnp_PayDate: str
    vnp_ResponseCode: str
    vnp_TmnCode: str
    vnp_TransactionNo: str
    vnp_TxnRef: str
    vnp_SecureHash: str


class PaymentResult(BaseModel):
    """Kết quả thanh toán"""
    success: bool
    order_id: str
    transaction_id: Optional[str] = None
    amount: Optional[int] = None
    message: str
    payment_method: PaymentMethod
    payment_status: PaymentStatus