from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.seat_reservations import SeatReservations
from app.models.seats import Seats
from app.models.showtimes import Showtimes
from app.schemas.reservations import SeatReservationsCreate, SeatReservationsResponse


def create_reservations(reservation_in : SeatReservationsCreate , db : Session):
    try:
        seat = db.query(Seats).filter(Seats.seat_id == reservation_in.seat_id).first()
        if not showtime:
            raise HTTPException(status_code=404 , detail="Showtime not found")
        showtime = db.query(Showtimes).filter(Showtimes.showtime_id == reservation_in.showtime_id).first()
        if not seat:
            raise HTTPException(status_code=404 , detail="Seat not found")
        existing_reservation = db.query(SeatReservations).filter(
            SeatReservations.showtime_id == reservation_in.showtime_id,
            SeatReservations.seat_id == reservation_in.seat_id,
             (
                SeatReservations.status == 'confirmed'
                | (SeatReservations.status == 'pending' and SeatReservations.expires_at > datetime.now(timezone.utc))
            )
        ).first()
        if existing_reservation:
            if existing_reservation.status == 'confirmed':
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail=f"Seat {reservation_in.seat_id} for showtime {reservation_in.showtime_id} is already confirmed."
                )
            elif existing_reservation.status == 'pending':
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Seat {reservation_in.seat_id} for showtime {reservation_in.showtime_id} is temporarily reserved and not yet expired."
                )
            
        current_utc_time = datetime.now(timezone.utc)
        calculated_expires_at = current_utc_time + timedelta(minutes=10)

        db_reservation = SeatReservations(
            seat_id=reservation_in.seat_id,
            showtime_id=reservation_in.showtime_id,
            user_id=reservation_in.user_id,
            session_id=reservation_in.session_id,
            expires_at=calculated_expires_at,
            status="pending"
        )

        db.add(db_reservation)
        db.commit()
        db.refresh(db_reservation) 

        return SeatReservationsResponse.from_orm(db_reservation)
    except Exception as e :
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail= e)
