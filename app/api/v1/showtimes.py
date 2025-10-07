from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.seat_layouts_service import *
from app.utils.response import success_response
from app.services.showtimes_service import (
    get_all_showtimes, 
    get_showtimes_by_theater, 
    get_showtimes_by_movie,
    get_showtimes_by_movie_and_theater,
    create_showtime
)
from app.schemas.showtimes import ShowtimesCreate
from typing import Optional
from datetime import date
router = APIRouter()

# Danh sách xuất chiếu trong rạp
@router.get("/showtimes")
def list_showtimes( db: Session = Depends(get_db)):
    showtimes = get_all_showtimes(db)
    return success_response(showtimes)

# Danh sách xuất chiếu trong rạp
@router.get("/showtimes/{theater_id}")
def list_showtimes_in_theater(theater_id: int, db: Session = Depends(get_db)):
    showtimes = get_showtimes_by_theater(db, theater_id)
    return success_response(showtimes)

# Danh sách xuất chiếu theo phim
@router.get("/movies/{movie_id}/showtimes")
def list_showtimes_by_movie(
    movie_id: int, 
    theater_id: Optional[int] = Query(None, description="Lọc theo theater_id"),
    show_date: Optional[date] = Query(None, description="Lọc theo ngày chiếu (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    showtimes = get_showtimes_by_movie(db, movie_id, theater_id, show_date)
    return success_response(showtimes)

# Danh sách xuất chiếu theo phim và rạp
@router.get("/movies/{movie_id}/theaters/{theater_id}/showtimes")
def list_showtimes_by_movie_and_theater(
    movie_id: int, 
    theater_id: int, 
    db: Session = Depends(get_db)
):
    showtimes = get_showtimes_by_movie_and_theater(db, movie_id, theater_id)
    return success_response(showtimes)

@router.post("/showtimes")
def add_showtime(showtime_in: ShowtimesCreate, db: Session = Depends(get_db)):
    showtime = create_showtime(db, showtime_in)
    return success_response(showtime)
