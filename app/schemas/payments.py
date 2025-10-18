from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PaymentMethod(str, Enum):
    VNPAY = "VNPAY"
    CASH = "CASH"
    MOMO = "MOMO"
    ZALO_PAY = "ZALO_PAY"
    BANK_TRANSFER = "BANK_TRANSFER"

class PaymentRequest(BaseModel):
    """Yêu cầu thanh toán"""
    session_id: Optional[str] = None
    order_desc: str
    payment_method: PaymentMethod
    language: str = "vn"


class PaymentResponse(BaseModel):
    """Phản hồi thanh toán"""
    payment_url: Optional[str] = None
    order_id: str
    amount: float
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    # expires_at: Optional[datetime] = None


class VNPayCallback(BaseModel):
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
    success: bool
    order_id: str
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    payment_url: Optional[str] = None
    expires_at: Optional[datetime] = None