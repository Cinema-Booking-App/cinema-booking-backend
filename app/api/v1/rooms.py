from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.rooms import RoomCreate
from app.services.rooms_service import create_room_to_theater, get_all_rooms, get_rooms_by_theater_id, get_room_by_id, get_seats_in_room
from app.utils.response import success_response

router = APIRouter()

# Lấy danh sách phòng theo ID của rạp
@router.get("/rooms")
async def get_rooms_by_theater(theater_id: Optional[int] = None, db: Session = Depends(get_db)):
    if theater_id is None:
        rooms = get_all_rooms(db)
    else:
        rooms = get_rooms_by_theater_id(db, theater_id)
    return success_response(rooms)

# Lấy thông tin phòng theo ID của phòng
@router.get("/rooms/{room_id}")
async def detail_room_by_id(room_id: int, db: Session = Depends(get_db)):
    room = get_room_by_id(db, room_id)
    return success_response(room)

# Tạo phòng cho rạp
@router.post("/theaters/{theater_id}/rooms")
def add_room_to_theater(theater_id: int, room_in: RoomCreate, db: Session = Depends(get_db)):
    room = create_room_to_theater(db, theater_id, room_in)
    return success_response(room)

# Xóa phòng theo ID
@router.delete("/rooms/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    return success_response(delete_room(db, room_id))

# Cập nhật thông tin phòng
@router.put("/rooms/{room_id}")
def update_room(room_id: int, room_in: RoomCreate, db: Session = Depends(get_db)):
    updated_room = update_room(db, room_id, room_in)
    return success_response(updated_room)


# Lấy danh sách ghế trong phòng
@router.get("/rooms/{room_id}/seats")
def get_all_seats_in_room(room_id: int, db: Session = Depends(get_db)):
    seats =  get_seats_in_room(db, room_id)
    return success_response(seats)