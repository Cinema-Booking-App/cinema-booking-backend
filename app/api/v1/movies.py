from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.movie_service import *
from app.schemas.movie import MovieCreate, MovieResponse, MovieUpdate
from fastapi import APIRouter

router = APIRouter()

# Lấy danh sách tất cả các phim
@router.get("/movies", response_model=List[MovieResponse])
def list_movies(db: Session = Depends(get_db)):
    return get_all_movies(db)

# Lấy chi tiết một phim theo ID
@router.get("/movies/{movie_id}",response_model=MovieResponse)
def detail_movie(movie_id: int, db: Session = Depends(get_db)):
    return get_movie_by_id(db, movie_id)

# Thêm một phim mới
@router.post("/movies")
def add_movie(movie_in: MovieCreate, db: Session = Depends(get_db)):
    return create_movie(db, movie_in)

# Xóa một phim theo ID
@router.delete("/movies/{movie_id}")
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    return delete_movie(db, movie_id)

# Cập nhật thông tin một phim theo ID
@router.put("/movies/{movie_id}")
def edit_movie(movie_id: int, movie_in: MovieUpdate, db: Session = Depends(get_db)):
    return update_movie(db, movie_id, movie_in)
