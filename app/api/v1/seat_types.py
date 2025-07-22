from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.seat_types import SeatTypeCreate
from app.services.seat_types_service import *
from app.utils.response import success_response


router = APIRouter()

# Lấy tất cả các loại ghế
@router.get("/seat_types")
def list_seat_types(db: Session = Depends(get_db)):
    return success_response(get_all_seat_types(db))

# Lấy thông tin loại ghế theo ID
@router.get("/seat_types/{seat_type_id}")
def detail_seat_type(seat_type_id: int, db: Session = Depends(get_db)):
    return success_response(get_seat_type_by_id(db, seat_type_id))

# Tạo loại ghế
@router.post("/seat_types")
def add_seat_type(seat_type_in: SeatTypeCreate, db: Session = Depends(get_db)):
    return success_response(create_seat_type(db, seat_type_in))

# Xóa loại ghế
@router.delete("/seat_types/{seat_type_id}")
def remove_seat_type(seat_type_id: int, db: Session = Depends(get_db)):
    return success_response(delete_seat_type(db, seat_type_id))

#Sửa loại ghế
@router.put("/seat_types/{seat_type_id}")
def edit_seat_type(seat_type_id: int, seat_type_in: SeatTypeCreate, db: Session = Depends(get_db)):
    return success_response(update_seat_type(db, seat_type_id, seat_type_in))