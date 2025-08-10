from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.users import Users
from app.services.movies_service import *
from app.schemas.movies import MovieCreate, MovieUpdate
from fastapi import APIRouter
from app.utils.response import success_response
from typing import Optional

router = APIRouter()


# Lấy danh sách tất cả các phim
@router.get("/movies")
def list_movies(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    search_query: Optional[str] = None,
    status: Optional[str] = None,
    # _ = Depends(get_current_active_user)
):
    return success_response(
        get_all_movies(
            db, skip=skip, limit=limit, search_query=search_query, status=status
        )
    )


# Lấy chi tiết một phim theo ID
@router.get("/movies/{movie_id}")
def detail_movie(movie_id: int, db: Session = Depends(get_db)):
    return success_response(get_movie_by_id(db, movie_id))


# Thêm một phim mới
@router.post("/movies")
def add_movie(movie_in: MovieCreate, db: Session = Depends(get_db)):
    return success_response(create_movie(db, movie_in))

    
# Xóa một phim theo ID
@router.delete("/movies/{movie_id}")
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    return success_response(delete_movie(db, movie_id))


# Cập nhật thông tin một phim theo ID
@router.put("/movies/{movie_id}")
def edit_movie(movie_id: int, movie_in: MovieUpdate, db: Session = Depends(get_db)):
    return success_response(update_movie(db, movie_id, movie_in))
