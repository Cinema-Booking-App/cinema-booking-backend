from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.schemas.users import  UserCreate
from app.services.users_service import *
from app.utils.response import success_response

router = APIRouter()

# Lấy danh sách tất cả người dùng
@router.get("/users")
def list_users(skip: int = 0, limit: int = 10, search_query: Optional[str] = None, db: Session = Depends(get_db)):
    return success_response(get_all_users(db, skip, limit, search_query))

# Lấy chi tiết một người dùng theo ID
@router.get("/users/{user_id}")
def detail_users(user_id: int, db: Session = Depends(get_db)):
    return success_response(get_user_by_id(db, user_id))

# Thêm mới một người dùng
@router.post("/users", status_code=201)
def create_new_user(user_in: UserCreate, db: Session = Depends(get_db)):
    return success_response(create_user(db, user_in))

#Xóa tài khoản người dùng
@router.delete("/users/{user_id}")
def delete_user_by_id(user_id: int, db: Session = Depends(get_db)):
    return success_response(delete_user(db, user_id))

#Cập nhật thông tin người dùng
@router.put("/users/{user_id}")
def update_user_by_id(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    return success_response(update_user(db, user_id, user_in))

# Cập nhật trạng thái người dùng
@router.put("/users/{user_id}/status")
def update_user_status_endpoint(user_id: int, status: UserStatusEnum, db: Session = Depends(get_db)):
    return success_response(update_user_status(db, user_id, status))

# Cập nhật điểm tích lũy
@router.put("/users/{user_id}/loyalty-points")
def update_loyalty_points_endpoint(user_id: int, points: int, db: Session = Depends(get_db)):
    return success_response(update_loyalty_points(db, user_id, points))

# Cập nhật tổng chi tiêu
@router.put("/users/{user_id}/total-spent")
def update_total_spent_endpoint(user_id: int, amount: float, db: Session = Depends(get_db)):
    return success_response(update_total_spent(db, user_id, amount))
