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
import qrcode
from io import BytesIO
from app.core.security import get_current_active_user, create_access_token
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


# Lấy danh sách vé của user
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

    result = []
    for t in tickets:
        showtime = t.showtime
        movie = showtime.movie
        room = showtime.room
        theater = showtime.theater

        result.append({
            "ticket_id": t.ticket_id,
            "booking_code": t.booking_code,
            "seat_code": t.seat.seat_code,
            "movie_title": movie.title,
            "poster_url": movie.poster_url,   # ✔ thêm poster
            "date": showtime.show_datetime.strftime("%Y-%m-%d"),  # ✔ thêm ngày
            "time": showtime.show_datetime.strftime("%H:%M"),      # ✔ thêm giờ
            "room": room.room_name,
            "theater_name": theater.name,      # ✔ tên rạp
            "theater_city": theater.city,      # (nếu muốn hiển thị thêm)
        })

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
# Lấy hình ảnh QR của vé (Trả về file ảnh PNG)
@router.get("/tickets/{ticket_id}/qr-image")
def get_ticket_qr_image(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Tickets).filter(Tickets.ticket_id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    showtime = ticket.showtime
    movie = showtime.movie
    room = showtime.room
    theater = showtime.theater
    user = ticket.user

    # 🔥 Payload đầy đủ thông tin vé
    payload = {
        "ticket_id": ticket.ticket_id,
        "booking_code": ticket.booking_code,
        "user_id": user.user_id if user else None,
        "user_name": user.full_name if user else None,
        "movie_title": movie.title,
        "seat_code": ticket.seat.seat_code,
        "seat_type": str(ticket.seat.seat_type),
        "showtime_id": showtime.showtime_id,
        "date": showtime.show_datetime.strftime("%Y-%m-%d"),
        "time": showtime.show_datetime.strftime("%H:%M"),
        "theater": theater.name,
        "room": room.room_name,
        "price": float(ticket.price),
        "type": "ticket_qr",
    }

    # 🔐 Tạo JWT từ full payload
    token = create_access_token(
        subject=str(ticket.ticket_id),
        expires_delta=timedelta(hours=12),
        extra_payload=payload  # ⭐ THÊM PAYLOAD VÀO JWT
    )

    # Tạo ảnh QR từ token
    qr = qrcode.make(token)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")
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