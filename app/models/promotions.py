from sqlalchemy import Column, Integer, String, Numeric, Date, Text, DateTime, func
from app.core.database import Base

class Promotions(Base):
    __tablename__ = "promotions"
    promotion_id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True)
    discount_percentage = Column(Numeric(5,2))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    max_usage = Column(Integer)
    used_count = Column(Integer, default=0)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now()) 