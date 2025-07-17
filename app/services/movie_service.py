from app.core.database import SessionLocal
from app.models.movie import Movie
from fastapi import APIRouter
from app.schemas.movie import MovieCreate, MovieOut

router = APIRouter()

# Lấy danh sách phim
def get_movies():
    db = SessionLocal() 
    movies = db.query(Movie).all()
    return [MovieOut.from_orm(m) for m in movies] 

# Lấy phim theo id 
def get_movie_by_id(movie_id):
    db = SessionLocal()
    try:
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if not movie:
            return None
        return movie
    finally:
        db.close()

# Thêm phim mới
def create_movie(movie_data :MovieCreate):
    db = SessionLocal()  
    try:
        db_movie = Movie(**movie_data.dict())
        db.add(db_movie)         
        db.commit()              # Lưu thay đổi vào database
        db.refresh(db_movie)     # Cập nhật lại đối tượng
        return db_movie
    except Exception as e:
        db.rollback()            # Nếu có lỗi, rollback transaction
        raise e
    finally:
        db.close()

# Xóa phim theo id
def delete_movie(movie_id):
    db = SessionLocal()
    try:
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if not movie:
            return None  
        db.delete(movie)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# Cập nhật thông tin phim theo id
def update_movie(movie_id, movie_data):
    db = SessionLocal()
    try:
        # Tìm phim theo id
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if not movie:
            return None  
        # Cập nhật các trường từ dữ liệu mới
        for key, value in movie_data.dict().items():
            setattr(movie, key, value)
        db.commit()
        db.refresh(movie)  # Làm mới đối tượng
        return movie  
    except Exception as e:
        db.rollback()  # Hủy thay đổi nếu lỗi
        raise e
    finally:
        db.close()  # Đóng session  