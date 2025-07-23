from sqlalchemy import Column, Integer, Enum, Numeric,func ,DateTime
from app.core.database import Base
import enum
class FormatTypeEnum(enum.Enum):
    TWO_D = "TWO_D"  # Sửa thành 'TWO_D'
    THREE_D = "THREE_D"  # Sửa thành 'THREE_D'
    IMAX = "IMAX"  # Sửa thành 'IMAX'
    FOUR_D = "4DX"  # Sửa thành '4DX'
    
class LanguageEnum(enum.Enum):
    sub_vi = "sub_vi" # là phụ đề tiếng Việt
    sub_en = "sub_en" # là phụ đề tiếng Anh
    dub_vi = "dub_vi" # là lồng tiếng Việt
    dub_en = "dub_en" # là lồng tiếng Anh
    original = "original" # là bản gốc không lồng tiếng

class StatusShowtimeEnum(enum.Enum):
    active = "active" # là trạng thái hoạt động bình thường
    inactive = "inactive" # là trạng thái không hoạt động
    sold_out = "sold_out" # là trạng thái đã bán hết vé

class Showtimes(Base):
    __tablename__ ="showtimes"
    showtime_id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, nullable=False)
    room_id = Column(Integer, nullable=False)
    show_datetime = Column(DateTime, nullable=False) # Ngày giờ chiếu phim ví dụ : Datetime sẽ là 2023-10-01 20:00:00
    format = Column(Enum(FormatTypeEnum ,name="format_type"), nullable=False, default=FormatTypeEnum.TWO_D ,server_default='TWO_D')
    ticket_price = Column(Numeric(10,2), nullable=False)
    status = Column(Enum(StatusShowtimeEnum), nullable=False, default=StatusShowtimeEnum.active ,server_default='active')
    language = Column(Enum(LanguageEnum), nullable=False, default=LanguageEnum.original ,server_default='original')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now()) 

