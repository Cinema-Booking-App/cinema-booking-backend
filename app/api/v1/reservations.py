from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reservations import SeatReservationsCreate
from app.services.reservations_service import  create_reserved_seats, get_reserved_seats
from app.utils.response import success_response

router = APIRouter()

#Danh sach các ghế đã đặt
@router.get("/reservations/{showtime_id}")
def list_reserved_seats(showtime_id: int, db: Session = Depends(get_db)):
    reserved_seats = get_reserved_seats(showtime_id, db)
    return success_response(reserved_seats)

#Tạo đặt chỗ
@router.post("/reservations")
def add_reservations(reservations_in : SeatReservationsCreate, db : Session = Depends(get_db)):
    reservations = create_reserved_seats(reservations_in, db)
    return success_response(reservations)

