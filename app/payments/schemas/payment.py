from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class PaymentMethodEnum(str, Enum):
    VNPAY = "vnpay"
    MOMO = "momo"
    ZALOPAY = "zalopay"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"

class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount")
    order_id: str = Field(..., description="Unique order identifier")
    description: str = Field(..., description="Payment description")
    payment_method: PaymentMethodEnum = Field(..., description="Payment method")
    return_url: str = Field(..., description="Return URL after payment")
    cancel_url: Optional[str] = Field(None, description="Cancel URL")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class PaymentResponse(BaseModel):
    success: bool = Field(..., description="Payment creation success")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    payment_url: Optional[str] = Field(None, description="Payment URL for redirect")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw provider response")

class PaymentCallback(BaseModel):
    payment_method: PaymentMethodEnum = Field(..., description="Payment method")
    callback_data: Dict[str, Any] = Field(..., description="Callback data from provider")

class PaymentVerificationResponse(BaseModel):
    success: bool = Field(..., description="Verification success")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw provider response")

class PaymentStatusResponse(BaseModel):
    transaction_id: str = Field(..., description="Transaction ID")
    status: PaymentStatusEnum = Field(..., description="Payment status")
    payment_method: PaymentMethodEnum = Field(..., description="Payment method")

class RefundRequest(BaseModel):
    transaction_id: str = Field(..., description="Transaction ID to refund")
    amount: Optional[float] = Field(None, gt=0, description="Refund amount (full refund if not specified)")
    reason: Optional[str] = Field(None, description="Refund reason")

class RefundResponse(BaseModel):
    success: bool = Field(..., description="Refund success")
    refund_id: Optional[str] = Field(None, description="Refund transaction ID")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw provider response")

class PaymentTransaction(BaseModel):
    """Database model schema for payment transactions"""
    id: Optional[int] = Field(None, description="Transaction ID")
    order_id: str = Field(..., description="Order ID")
    payment_method: PaymentMethodEnum = Field(..., description="Payment method")
    amount: float = Field(..., gt=0, description="Payment amount")
    status: PaymentStatusEnum = Field(..., description="Payment status")
    provider_transaction_id: Optional[str] = Field(None, description="Provider transaction ID")
    provider_response: Optional[Dict[str, Any]] = Field(None, description="Provider response data")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True