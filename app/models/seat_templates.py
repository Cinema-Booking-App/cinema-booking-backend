import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey ,Enum
from sqlalchemy.orm import relationship
from app.core.database import Base

class SeatTypeEnum(enum.Enum):
    regular  = "regular"
    vip = "vip"
    couple = "couple"

class SeatTemplates(Base):
    __tablename__ = "seat_templates"
    template_id = Column(Integer, primary_key=True, index=True)
    layout_id = Column(Integer, ForeignKey("seat_layouts.layout_id"), nullable=False)
    row_number = Column(Integer, nullable=False)
    column_number = Column(Integer, nullable=False)
    seat_code = Column(String(10), nullable=False)
    seat_type = Column(Enum(SeatTypeEnum , name="seat_type"), default=SeatTypeEnum.regular, server_default='regular')
    is_edge = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True) 

    # Thêm relationship với SeatLayout để lấy thông tin layout
    layout = relationship("SeatLayouts", back_populates="seat_templates")