from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.users_service import *
from app.utils.response import success_response

router = APIRouter();

# Lấy danh sách tất cả người dùng
@router.get("/users")
def list_users(skip: int = 0, limit: int = 10, search_query: Optional[str] = None, db: Session = Depends(get_db)):
    return success_response(get_all_users(db, skip, limit, search_query))

# Lấy chi tiết một người dùng theo ID
@router.get("/users/{user_id}")
def detail_users(user_id: int, db: Session = Depends(get_db)):
    return success_response(get_user_by_id(db, user_id))