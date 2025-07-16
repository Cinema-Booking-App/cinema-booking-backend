from sqlalchemy import Column, Integer, String, Text, Date, DateTime, CheckConstraint, func
from app.core.database import Base

class Movie(Base):

    __tablename__ = "movies"
    movie_id = Column(Integer, primary_key=True, index=True)  # ID duy nhất, tự tăng
    title = Column(String(255), nullable=False, index=True)  # Tên phim (bắt buộc)
    genre = Column(String(100))  # Thể loại phim
    duration = Column(Integer, nullable=False)  # Thời lượng (phút, bắt buộc)
    year = Column(Integer)  # Năm phát hành
    age_rating = Column(String(10))  # Độ tuổi: P, C13, C16, C18
    language = Column(String(50))  # Ngôn ngữ phim
    format = Column(String(50))  # Định dạng: 2D, 3D, IMAX
    description = Column(Text)  # Mô tả phim
    release_date = Column(Date)  # Ngày khởi chiếu
    trailer_url = Column(String(255))  # Link trailer
    poster_url = Column(String(255))  # Link poster
    status = Column(String(20), default='upcoming', server_default='upcoming')  # Trạng thái: upcoming, now_showing, ended
    director = Column(String(255))  # Đạo diễn
    actors = Column(Text)  # Diễn viên
    created_at = Column(DateTime, server_default=func.now())  # Thời gian tạo

    __table_args__ = (
        CheckConstraint("age_rating IN ('P', 'C13', 'C16', 'C18')", name='check_rating'),
        CheckConstraint("status IN ('upcoming', 'now_showing', 'ended')", name='check_status'),
    )