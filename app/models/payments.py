from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime, Enum, Text
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from sqlalchemy.orm import relationship


class PaymentStatusEnum(enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PaymentMethodEnum(enum.Enum):
    VNPAY = "VNPAY"
    CASH = "CASH"
    MOMO = "MOMO"
    ZALO_PAY = "ZALO_PAY"
    BANK_TRANSFER = "BANK_TRANSFER"


class Payment(Base):
    __tablename__ = "payments"
    __mapper_args__ = {
        'polymorphic_identity': 'payment',
        'polymorphic_on': 'payment_method'  # Sử dụng để phân biệt loại phương thức
    }
    payment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    transaction_id = Column(String(100), index=True, nullable=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(Enum(PaymentMethodEnum), nullable=False)
    payment_status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    payment_url = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Order information
    order_desc = Column(Text, nullable=True)
    client_ip = Column(String(45), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Mối quan hệ transactions và seat_reservations
    transactions = relationship("Transaction", back_populates="payment")
    seat_reservations = relationship("SeatReservations", back_populates="payment")

    def __repr__(self):
        return f"<Payment(id={self.id}, order_id={self.order_id}, status={self.payment_status})>"
    
class VNPayPayment(Payment):
    __tablename__ = "vnpay_payments"
    __mapper_args__ = {'polymorphic_identity': PaymentMethodEnum.VNPAY}

    payment_id = Column(Integer, ForeignKey('payments.payment_id'), primary_key=True)
    
    # Trường cụ thể cho VNPay
    vnp_txn_ref = Column(String(100), nullable=True)
    vnp_transaction_no = Column(String(100), nullable=True)
    vnp_bank_code = Column(String(20), nullable=True)
    vnp_card_type = Column(String(20), nullable=True)
    vnp_pay_date = Column(String(20), nullable=True)
    vnp_response_code = Column(String(10), nullable=True)