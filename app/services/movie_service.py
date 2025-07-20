from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.movie import Movie
from app.schemas.movie import MovieCreate, MovieUpdate, MovieResponse

# Lấy danh sách phim
def get_all_movies(db: Session):
    # Truy vấn tất cả các phim trong database
    movies = db.query(Movie).all()
    # Chuyển đổi sang schema MovieResponse
    return [MovieResponse.from_orm(m) for m in movies]

# Lấy phim theo id
def get_movie_by_id(db: Session, movie_id: int):
    # Truy vấn phim theo movie_id
    movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return MovieResponse.from_orm(movie)

# Thêm phim mới
def create_movie(db: Session, movie_in: MovieCreate):
    try:
        # Tạo đối tượng Movie từ dữ liệu đầu vào
        db_movie = Movie(**movie_in.dict())
        # Thêm vào session
        db.add(db_movie)
        # Lưu thay đổi vào database
        db.commit()
        # Làm mới đối tượng để lấy dữ liệu mới nhất từ DB
        db.refresh(db_movie)
        return db_movie
    except Exception as e:
        # Nếu có lỗi, rollback transaction
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")

# Xóa phim theo id
def delete_movie(db: Session, movie_id: int):
    try:
        # Tìm phim theo id
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        # Xóa phim khỏi session
        db.delete(movie)
        # Lưu thay đổi vào database
        db.commit()
        return True
    except Exception as e:
        # Nếu có lỗi, rollback transaction
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")

# Cập nhật thông tin phim theo id
def update_movie(db: Session, movie_id: int, movie_in: MovieUpdate):
    try:
        # Tìm phim theo id
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        # Cập nhật các trường từ dữ liệu mới ( exclude_unset=True , chỉ cập nhật trường được gửi lên)
        updated_movie = movie_in.dict(exclude_unset=True)
        for key, value in updated_movie.items():
            setattr(movie, key, value)
        # Lưu thay đổi vào database
        db.commit()
        # Làm mới đối tượng để lấy dữ liệu mới nhất từ DB
        db.refresh(movie)
        return movie
    except Exception as e:
        # Nếu có lỗi, rollback transaction
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Lỗi dữ liệu: {str(e)}"
        ) 