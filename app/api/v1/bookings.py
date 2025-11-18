from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.tickets_service import get_all_bookings, get_booking_by_code
from app.utils.response import success_response

router = APIRouter()


@router.get('/bookings')
def list_bookings(db: Session = Depends(get_db)):
    return success_response(get_all_bookings(db))


@router.get('/bookings/{booking_code}')
def get_booking(booking_code: str, db: Session = Depends(get_db)):
    return success_response(get_booking_by_code(db, booking_code))
