from app.core.database import Base
from sqlalchemy import Column, Integer, Date, Time, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func

class Showtimes(Base):
    __tablename__ = "showtimes"
    showtime_id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.movie_id"), nullable=False)
    screen_id = Column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    show_date = Column(Date, nullable=False)
    show_time = Column(Time, nullable=False)
    format = Column(String(50), nullable=False)
    ticket_price = Column(Numeric(10,2), nullable=False)
    created_at = Column(DateTime, server_default=func.now()) 