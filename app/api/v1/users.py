from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserResponse, UserCreate
from app.services.user_service import get_all_users, get_user_by_id, create_user


router = APIRouter();

# Lấy danh sách tất cả người dùng
@router.get("/users")
def list_users(db : Session = Depends(get_db)):
    return get_all_users(db);

# Lấy chi tiết một người dùng theo ID
@router.get("/users/{user_id}",response_model=UserResponse)
def detail_users(user_id: int, db: Session = Depends(get_db)):
    return get_user_by_id(db, user_id)

# Thêm mới một người dùng
@router.post("/users", response_model=UserResponse)
def create_new_user(user_in: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_in)
