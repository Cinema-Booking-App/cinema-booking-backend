from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(Enum):
    VNPAY = "vnpay"
    MOMO = "momo"
    ZALOPAY = "zalopay"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"

class PaymentResult:
    def __init__(
        self,
        success: bool,
        transaction_id: str = None,
        payment_url: str = None,
        error_message: str = None,
        raw_response: Dict[str, Any] = None
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.payment_url = payment_url
        self.error_message = error_message
        self.raw_response = raw_response or {}

class PaymentProvider(ABC):
    """Abstract base class for payment providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def create_payment(
        self,
        amount: float,
        order_id: str,
        description: str,
        return_url: str,
        cancel_url: str = None,
        metadata: Dict[str, Any] = None
    ) -> PaymentResult:
        """Create a payment transaction"""
        pass
    
    @abstractmethod
    def verify_payment(self, payment_data: Dict[str, Any]) -> PaymentResult:
        """Verify payment callback/webhook"""
        pass
    
    @abstractmethod
    def get_payment_status(self, transaction_id: str) -> PaymentStatus:
        """Get payment status by transaction ID"""
        pass
    
    @abstractmethod
    def refund_payment(
        self,
        transaction_id: str,
        amount: float = None,
        reason: str = None
    ) -> PaymentResult:
        """Refund a payment"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name"""
        pass