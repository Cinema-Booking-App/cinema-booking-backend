from fastapi import APIRouter, Request
from typing import List
from app.core.config import settings
from .services.payment_service import VNPayService
from .schemas.models import PaymentRequest, PaymentResponse, ReturnResponse, IPNResponse


router = APIRouter(prefix="/payments", tags=["payments"])


# Khởi tạo service
vnpay_service = VNPayService(
    tmn_code=settings.VNPAY_TMN_CODE,
    hash_secret=settings.VNPAY_HASH_SECRET,
    endpoint=settings.VNPAY_ENDPOINT
)

@router.get("/banks")
async def get_supported_banks():
    """Lấy danh sách ngân hàng được hỗ trợ."""
    return {"banks": vnpay_service.get_supported_banks()}

@router.post("/create", response_model=PaymentResponse)
async def create_vnpay_payment(payment_request: PaymentRequest):
    """Tạo URL thanh toán VNPay."""
    return vnpay_service.create_payment_url(payment_request.dict(), settings.VNPAY_RETURN_URL)

@router.get("/return", response_model=ReturnResponse)
async def vnpay_return(request: Request):
    """Xử lý redirect từ VNPay sau thanh toán."""
    params = dict(request.query_params)
    return vnpay_service.verify_return(params)

@router.post("/ipn", response_model=IPNResponse)
async def vnpay_ipn(request: Request):
    """Xử lý IPN từ VNPay."""
    params = dict(await request.form())
    return vnpay_service.verify_ipn(params)