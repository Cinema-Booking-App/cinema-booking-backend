from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class SeatLayouts(Base):
    __tablename__ = "seat_layouts"
    layout_id = Column(Integer, primary_key=True, index=True)
    layout_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text) 
    total_rows = Column(Integer, nullable=False)
    total_columns = Column(Integer, nullable=False)
    aisle_positions = Column(Text) 

    # Thêm relationship với SeatTemplate để có thể truy cập danh sách mẫu ghế
     # back_populates  để thiết lập quan hệ ngược từ SeatTemplate đến SeatLayout
    seat_templates = relationship("SeatTemplates", back_populates="layout", cascade="all, delete-orphan")