from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.seat_layouts_service import *
from app.utils.response import success_response


router = APIRouter()

@router.get("/seat_layout")
def list_seat_layouts(db: Session = Depends(get_db)):
    seat_layouts = get_all_seat_layouts(db)
    return success_response(seat_layouts)

# Lấy chi tiết layout ghế theo ID
@router.get("/seat_layout/{layout_id}")
def detail_seat_layout(layout_id: int, db: Session = Depends(get_db)):
    seat_layout = get_seat_layout_by_id(db, layout_id)
    return success_response(seat_layout)

# Tạo layout ghế
@router.post("/seat_layout")
def add_seat_layout(layout_in: SeatLayoutWithTemplatesCreate, db: Session = Depends(get_db)):
    return success_response(create_seat_layout_with_templates(db,layout_in))

# Xóa layout ghế
@router.delete("/seat_layout/{layout_id}")
def remove_seat_layout(layout_id: int, db: Session = Depends(get_db)):
    return success_response(delete_seat_layout(db, layout_id))
    
            