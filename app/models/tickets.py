import enum
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from app.core.database import Base
from sqlalchemy.orm import relationship

class TicketStatusEnum(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Tickets(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True, index=True)
    booking_code = Column(String(32), index=True, nullable=False)  # Mã đặt vé chung cho các vé cùng đơn
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    showtime_id = Column(Integer, ForeignKey("showtimes.showtime_id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.seat_id"), nullable=False)
    promotion_id = Column(Integer, ForeignKey("promotions.promotion_id"), nullable=True)
    price = Column(Numeric(10, 2, asdecimal=False), nullable=False)
    booking_time = Column(DateTime, server_default=func.now())
    status = Column(Enum(TicketStatusEnum), default=TicketStatusEnum.pending, server_default="pending")
    cancelled_at = Column(DateTime, nullable=True)
    # Thời điểm xác thực vé thành công (quét QR)
    # validated_at = Column(DateTime, nullable=True)

    # Quan hệ
    user = relationship("Users", back_populates="tickets")
    showtime = relationship("Showtimes", back_populates="tickets")
    seat = relationship("Seats", back_populates="tickets")
    promotions = relationship("Promotions", back_populates="tickets")
