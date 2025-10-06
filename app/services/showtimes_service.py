from sqlalchemy import desc, and_
from sqlalchemy.orm import Session, joinedload
from app.models.theaters import Theaters
from app.models.showtimes import Showtimes
from app.models.movies import Movies
from fastapi import HTTPException
from app.models.rooms import Rooms
from app.schemas.showtimes import ShowtimesCreate, ShowtimesResponse
from typing import Optional
from datetime import datetime, date


def get_all_showtimes(db: Session):
    # Sử dụng joinedload để tải trước dữ liệu từ các bảng liên quan
    showtimes = (
        db.query(Showtimes)
        .options(
            joinedload(Showtimes.movie),
            joinedload(Showtimes.theater),
            joinedload(Showtimes.room),
        )
        .order_by(desc(Showtimes.showtime_id))
        .all()
    )
    return showtimes

# Danh sách xuất chiếu trong rạp
def get_showtimes_by_theater(db: Session, theater_id: int):
    theater = db.query(Theaters).filter(Theaters.theater_id == theater_id).first()
    if not theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    # Lấy danh sách id phòng của rạp đó
    rooms = db.query(Rooms).filter(Rooms.theater_id == theater_id).all()
    # Lấy danh sách xuất chiếu theo id phòng
    showtimes = (
        db.query(Showtimes)
        .filter(Showtimes.room_id.in_([room.room_id for room in rooms]))
        .all()
    )
    return [ShowtimesResponse.from_orm(showtime) for showtime in showtimes]


# Danh sách xuất chiếu theo phim
def get_showtimes_by_movie(db: Session, movie_id: int, theater_id: Optional[int] = None, show_date: Optional[date] = None):
    movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    query = (
        db.query(Showtimes)
        .options(
            joinedload(Showtimes.movie),
            joinedload(Showtimes.theater),
            joinedload(Showtimes.room),
        )
        .filter(Showtimes.movie_id == movie_id)
    )
    
    # Lọc theo theater_id nếu có
    if theater_id:
        theater = db.query(Theaters).filter(Theaters.theater_id == theater_id).first()
        if not theater:
            raise HTTPException(status_code=404, detail="Theater not found")
        query = query.filter(Showtimes.theater_id == theater_id)
    
    # Lọc theo ngày nếu có
    if show_date:
        start_datetime = datetime.combine(show_date, datetime.min.time())
        end_datetime = datetime.combine(show_date, datetime.max.time())
        query = query.filter(
            and_(
                Showtimes.show_datetime >= start_datetime,
                Showtimes.show_datetime <= end_datetime
            )
        )
    
    showtimes = query.order_by(Showtimes.show_datetime).all()
    return showtimes


# Danh sách xuất chiếu theo phim và rạp
def get_showtimes_by_movie_and_theater(db: Session, movie_id: int, theater_id: int):
    movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    theater = db.query(Theaters).filter(Theaters.theater_id == theater_id).first()
    if not theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    
    showtimes = (
        db.query(Showtimes)
        .options(
            joinedload(Showtimes.movie),
            joinedload(Showtimes.theater),
            joinedload(Showtimes.room),
        )
        .filter(
            and_(
                Showtimes.movie_id == movie_id,
                Showtimes.theater_id == theater_id
            )
        )
        .order_by(Showtimes.show_datetime)
        .all()
    )
    return showtimes


def create_showtime(db: Session, showtime_in: ShowtimesCreate):
    try:
        showtime = Showtimes(**showtime_in.dict(exclude_unset=True))
        # Kiểm tra xem rạp có tồn tại không
        theater = (
            db.query(Theaters)
            .filter(Theaters.theater_id == showtime_in.theater_id)
            .first()
        )
        if not theater:
            raise HTTPException(status_code=404, detail="Theater not found")
        # Kiểm tra xem phòng có tồn tại không
        room = db.query(Rooms).filter(Rooms.room_id == showtime_in.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        # Kiểm tra xem xuất chiếu đã tồn tại chưa
        existing_showtime = (
            db.query(Showtimes)
            .filter(
                Theaters.theater_id == showtime_in.theater_id,
                Showtimes.room_id == showtime_in.room_id,
                Showtimes.show_datetime == showtime_in.show_datetime,
            )
            .first()
        )
        if existing_showtime:
            raise HTTPException(
                status_code=400,
                detail="Showtime already exists for this room at the specified time",
            )
        db.add(showtime)
        db.commit()
        db.refresh(showtime)
        return ShowtimesResponse.from_orm(showtime)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Xóa xuất chiếu theo id
def delete_showtime(db: Session, showtime_id: int):
    try:
        showtime = (
            db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
        )
        if not showtime:
            raise HTTPException(status_code=404, detail="Showtime not found")
        db.delete(showtime)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
