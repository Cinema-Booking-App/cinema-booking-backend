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
        "polymorphic_identity": "payment",
        "polymorphic_on": "payment_method",
    }

    payment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Đây là FK trỏ TỪ payments → transactions (1 payment thuộc về 1 transaction)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"), nullable=True)
    
    amount = Column(Float, nullable=False)
    payment_method = Column(Enum(PaymentMethodEnum, name="payment_method"), nullable=False)
    payment_status = Column(
        Enum(PaymentStatusEnum, name="payment_status"),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    payment_url = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    order_desc = Column(Text, nullable=True)
    client_ip = Column(String(45), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ==================== SỬA CHÍNH TẠI ĐÂY ====================
    # 1. Relationship đúng chiều: Payment → Transaction (1-1 hoặc nhiều-1)
    transaction = relationship(
        "Transaction",
        back_populates="payments",               # Transaction có nhiều payments
        foreign_keys=[transaction_id],            # bắt buộc chỉ rõ FK này
        uselist=False,                           # 1 payment chỉ thuộc 1 transaction
    )

    # 2. Nếu SeatReservations có cột payment_id trỏ ngược lại thì để thế này
    # (nếu không có thì comment lại cũng được)
    seat_reservations = relationship(
        "SeatReservations",
        back_populates="payment",
        foreign_keys="SeatReservations.payment_id",   
    )

    def __repr__(self):
        return f"<Payment {self.payment_id} | {self.order_id} | {self.payment_status.value}>"

class VNPayPayment(Payment):
    __tablename__ = "vnpay_payments"
    __mapper_args__ = {"polymorphic_identity": PaymentMethodEnum.VNPAY}

    payment_id = Column(Integer, ForeignKey("payments.payment_id"), primary_key=True)

    vnp_txn_ref = Column(String(100), nullable=True)
    vnp_transaction_no = Column(String(100), nullable=True)
    vnp_bank_code = Column(String(20), nullable=True)
    vnp_card_type = Column(String(20), nullable=True)
    vnp_pay_date = Column(String(50), nullable=True)
    vnp_response_code = Column(String(10), nullable=True)