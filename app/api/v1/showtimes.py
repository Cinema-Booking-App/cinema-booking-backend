from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.seat_layouts_service import *
from app.utils.response import success_response
from app.services.showtimes_service import get_showtimes_by_theater, create_showtime
from app.schemas.showtimes import ShowtimesCreate
router = APIRouter()

# Danh sách xuất chiếu trong rạp
@router.get("/showtimes/{theater_id}")
def list_showtimes_in_theater(theater_id: int, db: Session = Depends(get_db)):
    showtimes = get_showtimes_by_theater(db, theater_id)
    return success_response(showtimes)

@router.post("/showtimes")
def add_showtime(showtime_in: ShowtimesCreate, db: Session = Depends(get_db)):
    showtime = create_showtime(db, showtime_in)
    return success_response(showtime)
