from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.showtimes import ShowtimesCreate, ShowtimesUpdate, ShowtimesResponse
from app.services.showtimes_service import (
    get_all_showtimes, get_showtime_by_id, create_showtime, update_showtime, delete_showtime
)
from app.utils.response import success_response

router = APIRouter()

@router.get("/showtimes", response_model=list[ShowtimesResponse])
def list_showtimes(db: Session = Depends(get_db)):
    return success_response(get_all_showtimes(db))

@router.get("/showtimes/{showtime_id}", response_model=ShowtimesResponse)
def get_showtime(showtime_id: int, db: Session = Depends(get_db)):
    return success_response(get_showtime_by_id(db, showtime_id))

@router.post("/showtimes", response_model=ShowtimesResponse, status_code=201)
def create_new_showtime(showtime_in: ShowtimesCreate, db: Session = Depends(get_db)):
    return success_response(create_showtime(db, showtime_in))

@router.put("/showtimes/{showtime_id}", response_model=ShowtimesResponse)
def update_existing_showtime(showtime_id: int, showtime_in: ShowtimesUpdate, db: Session = Depends(get_db)):
    return success_response(update_showtime(db, showtime_id, showtime_in))

@router.delete("/showtimes/{showtime_id}")
def delete_existing_showtime(showtime_id: int, db: Session = Depends(get_db)):
    return success_response(delete_showtime(db, showtime_id)) 