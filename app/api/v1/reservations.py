from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.reservations import SeatReservationsCreate
from app.services.reservations_service import (
    create_reserved_seats, 
    get_reserved_seats, 
    create_multiple_reserved_seats,
    cancel_seat_reservations
)
from app.utils.response import success_response

router = APIRouter()

#Danh sach các ghế đã đặt
@router.get("/reservations/{showtime_id}")
def list_reserved_seats(showtime_id: int, db: Session = Depends(get_db)):
    reserved_seats = get_reserved_seats(showtime_id, db)
    return success_response(reserved_seats)

#Tạo đặt chỗ đơn lẻ
@router.post("/reservations")
def add_reservations(reservations_in : SeatReservationsCreate, db : Session = Depends(get_db)):
    reservations = create_reserved_seats(reservations_in, db)
    return success_response(reservations)

#Tạo nhiều đặt chỗ cùng lúc (realtime)
@router.post("/reservations/multiple")
async def add_multiple_reservations(reservations_in: List[SeatReservationsCreate], db: Session = Depends(get_db)):
    reservations = await create_multiple_reserved_seats(reservations_in, db)
    return success_response(reservations)

#Hủy đặt chỗ
@router.delete("/reservations/{showtime_id}")
async def cancel_reservations(
    showtime_id: int, 
    seat_ids: str,  # Comma-separated seat IDs
    session_id: str,
    db: Session = Depends(get_db)
):
    # Parse seat_ids from comma-separated string
    seat_id_list = [int(id.strip()) for id in seat_ids.split(',') if id.strip()]
    result = await cancel_seat_reservations(showtime_id, seat_id_list, session_id, db)
    return success_response(result)

