from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reservations import SeatReservationsCreate
from app.services.reservations_service import create_reservations
from app.utils.response import success_response

router = APIRouter()

@router.post("/reservations")
def add_reservations(reservations_in : SeatReservationsCreate, db : Session = Depends(get_db)):
    reservations = create_reservations(reservations_in, db)
    return success_response(reservations)

