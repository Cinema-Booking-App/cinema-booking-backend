from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.theaters_service import *
from app.schemas.theaters import TheaterCreate, TheaterUpdate
from fastapi import APIRouter
from app.utils.response import success_response

router = APIRouter()

# Lấy danh sách các rạp phim
@router.get("/theaters")
def list_theaters(db: Session = Depends(get_db)):
    return success_response(get_all_theaters(db))

# Lấy danh sách các thành phố khác nhau
@router.get("/theaters/cities")
def list_cities(db: Session = Depends(get_db)):
    return success_response(get_distinct_cities(db)) 
    
# Lấy chi tiết rạp phim theo ID
@router.get("/theaters/{theater_id}")
def detail_theater(theater_id: int, db: Session = Depends(get_db)):
    return success_response(get_theater_by_id(db, theater_id))

# Thêm rạp phim mới
@router.post("/theaters")
def add_theater(theater_in: TheaterCreate, db: Session = Depends(get_db)):
    return success_response(create_theater(db, theater_in))

# Xóa rạp phim theo ID
@router.delete("/theaters/{theater_id}")
def remove_theater(theater_id: int, db: Session = Depends(get_db)):
    return success_response(delete_theater(db, theater_id))

# Cập nhật thông tin rạp phim theo ID
@router.put("/theaters/{theater_id}")
def edit_theater(theater_id: int, theater_in: TheaterUpdate, db: Session = Depends(get_db)):
    return success_response(update_theater(db, theater_id, theater_in))

@router.get("/theaters/{theater_id}/rooms")
def read_rooms_by_theater(theater_id: int,db: Session = Depends(get_db)):
    return success_response(get_rooms_by_theater_id(db, theater_id))