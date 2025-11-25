from typing import Optional
from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.movies import Movies
from app.schemas.common import PaginatedResponse
from app.schemas.movies import MovieCreate, MovieUpdate, MovieResponse
from app.core.redis_client import redis_client
import json


# Lấy danh sách phim

def get_all_movies(
    db: Session,                      
    skip: int = 0,                    
    limit: int = 10,                 
    search_query: Optional[str] = None,
    status: Optional[str] = None,   
): 

    # Redis cache key
    cache_key = f"movies:{skip}:{limit}:{search_query}:{status}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            print(f"[REDIS] Đọc cache: {cache_key}")
            return PaginatedResponse(**json.loads(cached))
    except Exception as e:
        print(f"[REDIS] Lỗi khi đọc cache: {e}")

    query = db.query(Movies).order_by(desc(Movies.movie_id))
    if search_query:
        query = query.filter(Movies.title.ilike(f"%{search_query}%"))
    if status and status != "all":
        query = query.filter(Movies.status == status)
    total = query.count()
    movies = query.offset(skip).limit(limit).all()
    movies_response = [MovieResponse.from_orm(m) for m in movies]
    result = PaginatedResponse(total=total, skip=skip, limit=limit, items=movies_response)
    # Cache result for 5 minutes
    try:
        redis_client.setex(cache_key, 300, json.dumps(result.model_dump(), default=str))
        print(f"[REDIS] Ghi cache: {cache_key}")
    except Exception as e:
        print(f"[REDIS] Lỗi khi ghi cache: {e}")
    return result

# Lấy phim theo id
def get_movie_by_id(db: Session, movie_id: int):

    cache_key = f"movie:{movie_id}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            print(f"[REDIS] Đọc cache: {cache_key}")
            return MovieResponse(**json.loads(cached))
    except Exception as e:
        print(f"[REDIS] Lỗi khi đọc cache: {e}")

    movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    result = MovieResponse.from_orm(movie)
    try:
        redis_client.setex(cache_key, 300, json.dumps(result.model_dump(), default=str))
        print(f"[REDIS] Ghi cache: {cache_key}")
    except Exception as e:
        print(f"[REDIS] Lỗi khi ghi cache: {e}")
    return result


# Thêm phim mới
def create_movie(db: Session, movie_in: MovieCreate):
    try:
        # Tạo đối tượng Movie từ dữ liệu đầu vào
        db_movie = Movies(**movie_in.dict(exclude_unset=True))
        # Thêm vào session
        db.add(db_movie)
        # Lưu thay đổi vào database
        db.commit()
        # Làm mới đối tượng để lấy dữ liệu mới nhất từ DB
        db.refresh(db_movie)
        # Invalidate movies cache
        try:
            redis_client.delete_pattern("movies:*")
        except Exception as e:
            print(f"[REDIS] Lỗi khi xóa cache: {e}")
        return db_movie
    except Exception as e:
        # Nếu có lỗi, rollback transaction
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")


# Xóa phim theo id
def delete_movie(db: Session, movie_id: int):
    try:
        # Tìm phim theo id
        movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        # Xóa phim khỏi session
        db.delete(movie)
        # Lưu thay đổi vào database
        db.commit()
        # Invalidate movies and movie cache
        try:
            redis_client.delete_pattern("movies:*")
            redis_client.delete(f"movie:{movie_id}")
        except Exception as e:
            print(f"[REDIS] Lỗi khi xóa cache: {e}")
        return True
    except Exception as e:
        # Nếu có lỗi, rollback transaction
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")


# Import nhiều phim cùng lúc
def bulk_create_movies(db: Session, movies_in: list[MovieCreate]):
    created_movies = []
    failed_movies = []
    
    print(f"Starting import of {len(movies_in)} movies...")
    
    for i, movie_data in enumerate(movies_in):
        try:
            print(f"Processing movie {i+1}: {movie_data.title}")
            # Tạo đối tượng Movie từ dữ liệu đầu vào
            movie_dict = movie_data.dict(exclude_unset=True)
            print(f"Movie data: {movie_dict}")
            
            db_movie = Movies(**movie_dict)
            db.add(db_movie)
            db.flush()  # Flush để lấy ID nhưng chưa commit
            
            print(f"Movie {movie_data.title} added with ID: {db_movie.movie_id}")
            
            created_movies.append({
                "title": db_movie.title,
                "movie_id": db_movie.movie_id,
                "status": "success"
            })
        except Exception as e:
            print(f"Error creating movie {movie_data.title}: {str(e)}")
            # Rollback transaction hiện tại để tiếp tục với movie tiếp theo
            db.rollback()
            # Bắt đầu transaction mới
            db.begin()
            failed_movies.append({
                "title": movie_data.title,
                "error": str(e),
                "status": "failed"
            })
    
    # Commit tất cả các phim thành công
    try:
        print(f"Committing {len(created_movies)} movies to database...")
        db.commit()
        print("Commit successful!")
    except Exception as e:
        print(f"Commit failed: {str(e)}")
        db.rollback()
    
    result = {
        "total": len(movies_in),
        "success": len(created_movies),
        "failed": len(failed_movies),
        "created_movies": created_movies,
        "failed_movies": failed_movies
    }
    print(f"Import result: {result}")
    # Invalidate movies cache
    try:
        redis_client.delete_pattern("movies:*")
    except Exception as e:
        print(f"[REDIS] Lỗi khi xóa cache: {e}")
    return result


# Cập nhật thông tin phim theo id
def update_movie(db: Session, movie_id: int, movie_in: MovieUpdate):
    try:
        # Tìm phim theo id
        movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        # Cập nhật các trường từ dữ liệu mới ( exclude_unset=True , chỉ cập nhật trường được gửi lên)
        updated_movie = movie_in.dict(exclude_unset=True)
        for key, value in updated_movie.items():
            setattr(movie, key, value)
        # Lưu thay đổi vào database
        db.commit()
        db.refresh(movie)
        # Invalidate movies and movie cache
        try:
            redis_client.delete_pattern("movies:*")
            redis_client.delete(f"movie:{movie_id}")
        except Exception as e:
            print(f"[REDIS] Lỗi khi xóa cache: {e}")
        return movie
    except Exception as e:
        # Nếu có lỗi, rollback transaction
        db.rollback()
        raise HTTPException(status_code=400, detail=f" {str(e)}")
