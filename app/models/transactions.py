import enum
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from app.core.database import Base
from sqlalchemy.orm import relationship


class TransactionStatus(enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    staff_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)  # Nhân viên thực hiện giao dịch
    promotion_id = Column(Integer, ForeignKey("promotions.promotion_id"), nullable=True)
    total_amount = Column(Numeric(10, 2, asdecimal=False), nullable=False)
    payment_method = Column(String(255), nullable=False)
    transaction_time = Column(DateTime, server_default=func.now())
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending, server_default="pending")
    payment_ref_code = Column(String(255), nullable=True)

    # Quan hệ
    payment_id = Column(Integer, ForeignKey("payments.payment_id"), nullable=True)
    payment = relationship("Payment", back_populates="transactions")

    user = relationship("Users", back_populates="transactions", foreign_keys=[user_id])
    staff = relationship("Users", foreign_keys=[staff_user_id]) 

