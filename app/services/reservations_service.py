from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.seat_reservations import SeatReservations
from app.models.seats import Seats
from app.models.showtimes import Showtimes
from app.schemas.reservations import SeatReservationsCreate, SeatReservationsResponse


#Lấy danh sách các ghế đã đặt
def get_reserved_seats(showtime_id: int, db: Session):
    try:
        showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
        if not showtime:
            raise HTTPException(status_code=404, detail="Showtime not found")
        # Lấy danh sách các ghế đã đặt cho showtime cụ thể
        reserved_seats = db.query(SeatReservations).filter(
            SeatReservations.showtime_id == showtime_id,
            SeatReservations.status.in_(["confirmed", "pending"])
        ).all()
        
        return [SeatReservationsResponse.from_orm(reservation) for reservation in reserved_seats]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# Tạo một hàm để tạo đặt chỗ
def create_reserved_seats(reservation_in : SeatReservationsCreate , db : Session):
    try:
        showtime = db.query(Showtimes).filter(Showtimes.showtime_id == reservation_in.showtime_id).first()
        seat = db.query(Seats).filter(Seats.seat_id == reservation_in.seat_id).first()
        if not showtime:
            raise HTTPException(status_code=404 , detail="Showtime not found")
        if not seat:
            raise HTTPException(status_code=404 , detail="Seat not found")
        existing_reservation = db.query(SeatReservations).filter(
            SeatReservations.showtime_id == reservation_in.showtime_id,
            SeatReservations.seat_id == reservation_in.seat_id,
            or_(
                SeatReservations.status == 'confirmed',
                and_(
                    SeatReservations.status == 'pending',
                    SeatReservations.expires_at > datetime.now(timezone.utc)
                )
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


#Xóa đặt chỗ tự động khi hết hạn
def delete_expired_reservations(db: Session):
    try:
        current_time = datetime.now(timezone.utc)
        expired_reservations = db.query(SeatReservations).filter(
            SeatReservations.status == 'pending',
            SeatReservations.expires_at < current_time
        ).all()

        for reservation in expired_reservations:
            db.delete(reservation)

        db.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))