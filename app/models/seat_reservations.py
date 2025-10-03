from sqlalchemy import Column, Integer, String, DateTime, text, UniqueConstraint
from app.core.database import Base

class SeatReservations(Base):
    __tablename__ = "seat_reservations"
    reservation_id = Column(Integer, primary_key=True, autoincrement=True) 
    seat_id = Column(Integer, nullable=False)
    showtime_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=True) 
    session_id = Column(String(255), nullable=True) 
    reserved_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    expires_at = Column(DateTime(timezone=True), nullable=False) 
    status = Column(String(50), nullable=False, default="pending") 
    transaction_id = Column(Integer, nullable=True)
    __table_args__ = (UniqueConstraint('seat_id', 'showtime_id'),)