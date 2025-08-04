from app.core.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func

class Rooms(Base):
    __tablename__ = "rooms"

    room_id = Column(Integer, primary_key=True, index=True)
    layout_id = Column(Integer, ForeignKey("seat_layouts.layout_id"))
    theater_id = Column(Integer, ForeignKey("theaters.theater_id"))
    room_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
