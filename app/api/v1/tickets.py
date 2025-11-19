from fastapi import APIRouter, Depends
from app.core.security import get_current_active_user
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.tickets import TicketsCreate, TicketVerifyRequest
from app.services.tickets_service import create_ticket_directly, generate_ticket_qr, verify_ticket_qr
from app.utils.response import success_response


router =APIRouter()

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
