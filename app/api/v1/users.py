from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.users import  UserCreate
from app.services.users_service import *
from app.utils.response import success_response

router = APIRouter();

# Lấy danh sách tất cả người dùng
@router.get("/users")
def list_users(db : Session = Depends(get_db)):
    return success_response(get_all_users(db));

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