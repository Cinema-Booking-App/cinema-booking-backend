# dashboard.py
# API cho dashboard thống kê hệ thống
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Trả về thống kê tổng quan hệ thống: số lượng user, vé, doanh thu, v.v.
    """
    # Ví dụ: lấy tổng số user, tổng số vé, tổng doanh thu
    from app.models.users import Users
    from app.models.tickets import Tickets
    from app.models.payments import Payment , PaymentStatusEnum
    user_count = db.query(Users).count()
    ticket_count = db.query(Tickets).count()
    total_revenue = db.query(Payment).filter(Payment.payment_status == PaymentStatusEnum.SUCCESS).with_entities(Payment.amount).all()
    total_revenue = sum([p.amount for p in total_revenue]) if total_revenue else 0
    return {
        "user_count": user_count,
        "ticket_count": ticket_count,
        "total_revenue": total_revenue
    }
