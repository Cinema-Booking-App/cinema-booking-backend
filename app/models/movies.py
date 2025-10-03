import enum
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, func, Enum
from app.core.database import Base

class AgeRatingEnum(enum.Enum):
    P = 'P'
    C13 = 'C13'
    C16 = 'C16'
    C18 = 'C18'

class MovieStatusEnum(enum.Enum):
    upcoming = 'upcoming'
    now_showing = 'now_showing'
    ended = 'ended'

class Movies(Base):
    __tablename__ = "movies"
    movie_id = Column(Integer, primary_key=True, index=True)  # ID duy nhất, tự tăng
    title = Column(String(255), nullable=False, index=True)  # Tên phim (bắt buộc)
    genre = Column(String(100))  # Thể loại phim
    duration = Column(Integer, nullable=False)  # Thời lượng (phút, bắt buộc)
    age_rating = Column(Enum(AgeRatingEnum), nullable=True)  # Độ tuổi: P, C13, C16, C18
    description = Column(Text)  # Mô tả phim
    release_date = Column(Date)  # Ngày khởi chiếu
    trailer_url = Column(String(255))  # Link trailer
    poster_url = Column(String(255))  # Link poster
    status = Column(Enum(MovieStatusEnum), default=MovieStatusEnum.upcoming, server_default='upcoming')  # Trạng thái: upcoming, now_showing, ended
    director = Column(String(255))  # Đạo diễn
    actors = Column(Text)  # Diễn viên
    created_at = Column(DateTime, server_default=func.now())  # Thời gian tạo
