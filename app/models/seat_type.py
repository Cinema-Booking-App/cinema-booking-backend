from sqlalchemy import Column, Integer, String, Numeric, Text
from sqlalchemy.sql import text
from app.core.database import Base

class SeatType(Base):
    __tablename__ = "seat_types"
    seat_type_id = Column(Integer, primary_key=True, index=True)
    type_name  = Column(String(255), unique=True, nullable=False)
    price_multiplier = Column(Numeric(4, 2), nullable=False, server_default=text("1.00"))
    additional_fee = Column(Numeric(10,2), nullable=False, server_default=text("0.00"))
    note  = Column(Text)