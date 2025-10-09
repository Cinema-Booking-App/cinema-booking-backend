from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class PaymentStatusEnum(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethodEnum(enum.Enum):
    VNPAY = "vnpay"
    CASH = "cash"


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    transaction_id = Column(String(100), index=True, nullable=True)
    amount = Column(Integer, nullable=False)  # Amount in VND
    payment_method = Column(Enum(PaymentMethodEnum), nullable=False)
    payment_status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING)
    
    # VNPay specific fields
    vnp_txn_ref = Column(String(100), nullable=True)
    vnp_transaction_no = Column(String(100), nullable=True)
    vnp_bank_code = Column(String(20), nullable=True)
    vnp_card_type = Column(String(20), nullable=True)
    vnp_pay_date = Column(String(20), nullable=True)
    vnp_response_code = Column(String(10), nullable=True)
    
    # Order information
    order_desc = Column(Text, nullable=True)
    client_ip = Column(String(45), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys (if you have reservation/booking tables)
    # reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=True)
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    # reservation = relationship("Reservation", back_populates="payments")
    # user = relationship("User", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, order_id={self.order_id}, status={self.payment_status})>"