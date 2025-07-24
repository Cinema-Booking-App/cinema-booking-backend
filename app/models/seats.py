from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, func
from app.core.database import Base
from app.models.seat_templates import SeatTypeEnum

class Seats(Base):
    __tablename__ = "seats"
    seat_id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, nullable=False)
    seat_type = Column(Enum(SeatTypeEnum , name="seat_type"), default=SeatTypeEnum.regular, server_default='regular')
    is_available =  Column(Boolean, default=True)
    seat_code = Column(String(10), nullable=False)
    row_number = Column(Integer, nullable=False)
    column_number = Column(Integer, nullable=False)
    seat_code = Column(String(10), nullable=False)
    is_edge = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
