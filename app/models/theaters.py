from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base

class Theaters(Base):
    __tablename__ = "theaters"
    theater_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), index=True)
    phone = Column(String(20))
    created_at = Column(DateTime, server_default=func.now()) 