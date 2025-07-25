from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.tickets import TicketsCreate
from app.services.tickets_service import create_ticket_directly


router =APIRouter()

# Nhân viên Tạo vé trực tiếp tại quầy
@router.post("/tickets/direct",status_code=201)
def add_ticket_directly(ticket_in : TicketsCreate , db : Session = Depends(get_db)):
    return create_ticket_directly(ticket_in=ticket_in ,db=db)
