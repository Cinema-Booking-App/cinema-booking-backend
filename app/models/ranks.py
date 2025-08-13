from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class Ranks(Base):
    __tablename__ = 'ranks'

    rank_id = Column(Integer, primary_key=True, autoincrement=True, index=True)  # ID tự tăng
    rank_name = Column(String(50), nullable=False)  # Tên cấp bậc
    spending_target = Column(Numeric(15, 2), nullable=False)  # Tổng chi tiêu yêu cầu (VND)
    ticket_percent = Column(Numeric(5, 2), nullable=False)  # % tích lũy khi mua vé
    combo_percent = Column(Numeric(5, 2), nullable=False)  # % tích lũy khi mua combo
    is_default = Column(Boolean, default=True)  # Cấp mặc định hay không
    created_at = Column(DateTime, server_default=func.now())  # Ngày tạo
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # Ngày cập nhật
