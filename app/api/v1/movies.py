from fastapi import APIRouter
from app.schemas.movie import MovieCreate
from app.services.movie_service import *

router = APIRouter()

# Lấy danh sách tất cả các phim
@router.get("/movies")
def list_movies():
    return get_movies();

# Lấy phim theo id 
@router.get("/movies/{movie_id}")
def detail_movie(movie_id: int):
    return get_movie_by_id(movie_id)

# Thêm một phim mới
@router.post("/movies")
def add_movie(movie : MovieCreate):
    return create_movie(movie)

# Xóa một phim theo id
@router.delete("/movies/{movie_id}")
def remove_movie(movie_id : int):
    return delete_movie(movie_id)

# Cập nhật thông tin một phim theo id
@router.put("/movies/{movie_id}")
def edit_movie(movie_id : int, movie : MovieCreate):
    return update_movie(movie_id,movie)
