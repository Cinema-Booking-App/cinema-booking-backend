import datetime
from fastapi import APIRouter, Depends
from app.core.security import get_current_active_user
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.tickets import TicketsCreate, TicketVerifyRequest
from app.services.tickets_service import create_ticket_directly, generate_ticket_qr, verify_ticket_qr ,get_all_bookings
from app.utils.response import success_response
from app.models.users import Users
from app.models.tickets import Tickets  
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from app.core.token_utils import create_token
from datetime import timedelta


router =APIRouter()
@router.get("/tickets")
def read_tickets(
    db: Session = Depends(get_db),
    # _ = Depends(get_current_active_user),
):
    # Placeholder for reading tickets logic
    return success_response(get_all_bookings(db))

# Nhân viên Tạo vé trực tiếp tại quầy
@router.post("/tickets/direct",status_code=201)
def add_ticket_directly(
    ticket_in : TicketsCreate,
    db : Session = Depends(get_db),
    # _ = Depends(get_current_active_user),
):
    return create_ticket_directly(ticket_in=ticket_in ,db=db)


# Tạo QR token cho vé
@router.post("/tickets/{ticket_id}/qr")
def create_ticket_qr(
    ticket_id: int,
    db: Session = Depends(get_db),
    # _ = Depends(get_current_active_user),
):
    return success_response(generate_ticket_qr(db, ticket_id))


# Quét/kiểm tra QR và xác thực vé
@router.post("/tickets/verify-qr")
def verify_ticket_by_qr(
    verify_in: TicketVerifyRequest,
    db: Session = Depends(get_db),
    # _ = Depends(get_current_active_user),
):
    return success_response(verify_ticket_qr(db, verify_in))


@router.get("/tickets/my")
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_active_user)
):
    tickets = (
        db.query(Tickets)
        .filter(Tickets.user_id == current_user.user_id)
        .all()
    )

    bookings = {}

    for t in tickets:
        code = t.booking_code

        if code not in bookings:
            showtime = t.showtime
            movie = showtime.movie
            room = showtime.room
            theater = showtime.theater

            bookings[code] = {
                "booking_code": code,
                "movie_title": movie.title,
                "poster_url": movie.poster_url,
                "date": showtime.show_datetime.strftime("%Y-%m-%d"),
                "time": showtime.show_datetime.strftime("%H:%M"),
                "room": room.room_name,
                "theater_name": theater.name,
                "theater_city": theater.city,
                "seats": [],
                "qr_code": t.qr_code,
                # Dùng trực tiếp show_datetime để sort, không trả ra FE
                "_sort": showtime.show_datetime
            }

        bookings[code]["seats"].append(t.seat.seat_code)

    result = list(bookings.values())

    # Sort mới nhất → cũ nhất
    result.sort(key=lambda x: x["_sort"], reverse=True)

    # Xóa key sort trước khi trả về
    for item in result:
        del item["_sort"]

    return success_response(result)

# Lấy chi tiết vé
@router.get("/tickets/{ticket_id}")
def get_ticket_detail(ticket_id: int, db: Session = Depends(get_db)):
    ticket = (
        db.query(Tickets)
        .filter(Tickets.ticket_id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    showtime = ticket.showtime
    movie = showtime.movie
    theater = showtime.theater
    room = showtime.room
    seat = ticket.seat

    return success_response({
        "ticket_id": ticket.ticket_id,
        "booking_code": ticket.booking_code,
        "movie_title": movie.title,
        "poster_url": movie.poster_url,
        "date": showtime.show_datetime.strftime("%Y-%m-%d"),
        "time": showtime.show_datetime.strftime("%H:%M"),
        
        "seat_code": seat.seat_code,
        "price": float(ticket.price),

        # Theater info – FIXED
        "theater_name": theater.name,
        "theater_address": theater.address,
        "theater_city": theater.city,

        # Room info
        "room_name": getattr(room, "room_name", None)
    })
# Hủy vé
@router.post("/tickets/{ticket_id}/cancel")
def cancel_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_active_user),
):
    ticket = db.query(Tickets).filter(
        Tickets.ticket_id == ticket_id,
        Tickets.user_id == current_user.user_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.status == "cancelled":
        raise HTTPException(status_code=400, detail="Ticket already cancelled")

    ticket.status = "cancelled"
    ticket.cancelled_at = datetime.now()

    if ticket.transaction:
        ticket.transaction.status = "refunded"

    db.commit()

    return success_response({"message": "Ticket cancelled successfully"})