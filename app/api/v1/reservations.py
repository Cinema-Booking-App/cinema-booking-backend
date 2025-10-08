from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.reservations import SeatReservationsCreate, CancelReservationRequest
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

# Test endpoint để debug
@router.get("/reservations/test")
async def test_endpoint():
    return {"message": "Reservations API is working", "timestamp": "2025-10-08"}

#Hủy đặt chỗ
@router.post("/reservations/cancel")
async def cancel_reservations(
    cancel_request: CancelReservationRequest,
    db: Session = Depends(get_db)
):
    try:
        print(f"🔄 Received cancel request: {cancel_request}")
        result = await cancel_seat_reservations(
            showtime_id=cancel_request.showtime_id,
            seat_ids=cancel_request.seat_ids,
            session_id=cancel_request.session_id,
            db=db
        )
        print(f"✅ Cancel result: {result}")
        return success_response(result)
    except HTTPException as he:
        print(f"❌ HTTP Exception: {he}")
        raise he
    except Exception as e:
        print(f"❌ General Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

