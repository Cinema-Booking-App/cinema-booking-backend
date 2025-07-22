from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.theaters import Theaters
from app.schemas.theaters import TheaterCreate, TheaterUpdate, TheaterResponse

def get_all_theaters(db: Session):
    theaters = db.query(Theaters).all()
    return [TheaterResponse.from_orm(t) for t in theaters]

def get_theater_by_id(db: Session, theater_id: int):
    theater = db.query(Theaters).filter(Theaters.theater_id == theater_id).first()
    if not theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    return TheaterResponse.from_orm(theater)

def create_theater(db: Session, theater_in: TheaterCreate):
    try:
        db_theater = Theaters(**theater_in.dict())
        db.add(db_theater)
        db.commit()
        db.refresh(db_theater)
        return db_theater
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")

def delete_theater(db: Session, theater_id: int):
    try:
        theater = db.query(Theaters).filter(Theaters.theater_id == theater_id).first()
        if not theater:
            raise HTTPException(status_code=404, detail="Theater not found")
        db.delete(theater)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")

def update_theater(db: Session, theater_id: int, theater_in: TheaterUpdate):
    try:
        theater = db.query(Theaters).filter(Theaters.theater_id == theater_id).first()
        if not theater:
            raise HTTPException(status_code=404, detail="Theater not found")
        updated_theater = theater_in.dict(exclude_unset=True)
        for key, value in updated_theater.items():
            setattr(theater, key, value)
        db.commit()
        db.refresh(theater)
        return theater
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")

# Lây danh sách các thành phố khác nhau
def get_distinct_cities(db: Session):
    result = db.query(Theaters.city).distinct().all()
    # Lấy ra danh sách city, loại bỏ None nếu cần
    return [row.city for row in result if row.city] 