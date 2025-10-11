from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.payments_service import PaymentService
from app.schemas.payments import PaymentRequest
from app.utils.response import success_response

router = APIRouter()
payment_service = PaymentService()

# Tạo thanh toán từ reservation
@router.post("/vnpay/create-payment-from-reservation")
async def create_vnpay_payment_from_reservation(
    reservation_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Tạo thanh toán VNPay từ reservation ID"""
    try:
        # Lấy địa chỉ IP của client
        client_ip = request.client.host
        
        # Gọi service để xử lý
        result = payment_service.create_payment_from_reservation(
            db=db,
            reservation_id=reservation_id,
            client_ip=client_ip
        )
        
        return success_response(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Tạo thanh toán VNPay
@router.post("/vnpay/create-payment")
async def create_vnpay_payment(
    payment_request: PaymentRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Lấy địa chỉ IP của client
        client_ip = request.client.host
        
        # Tạo bản ghi thanh toán
        payment_service.create_payment_record(
            db=db,
            order_id=payment_request.order_id,
            amount=payment_request.amount,
            payment_method="vnpay",
            order_desc=payment_request.order_desc,
            client_ip=client_ip
        )
        
        # Tạo URL thanh toán VNPay
        payment_response = payment_service.create_vnpay_payment_url(payment_request, client_ip)
        
        return payment_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/vnpay/return")
async def vnpay_return_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle VNPay return callback (when user returns from VNPay)
    """
    try:
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Process return callback
        payment_result = payment_service.handle_vnpay_callback(query_params)
        
        # Update payment status and process ticket creation
        result = payment_service.update_payment_status(db, payment_result.order_id, payment_result)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/vnpay/ipn")
async def vnpay_ipn_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle VNPay IPN (Instant Payment Notification) callback
    This endpoint is called by VNPay to notify payment status
    """
    try:
        # Get query parameters (VNPay sends data as query parameters)
        query_params = dict(request.query_params)
        
        # Process IPN callback
        payment_result = payment_service.handle_vnpay_callback(query_params)
        
        # Update payment status and process ticket creation
        result = payment_service.update_payment_status(db, payment_result.order_id, payment_result)
        
        # Return response to VNPay
        if payment_result.success:
            return JSONResponse(
                content={'RspCode': '00', 'Message': 'Confirm Success'},
                status_code=200
            )
        else:
            return JSONResponse(
                content={'RspCode': '99', 'Message': 'Unknow error'},
                status_code=200
            )
            
    except HTTPException:
        raise
    except Exception as e:
        # Always return success to VNPay to avoid retry
        return JSONResponse(
            content={'RspCode': '99', 'Message': 'Unknow error'},
            status_code=200
        )


# TODO: Implement query và refund endpoints sau khi cần thiết


@router.get("/payment-status/{order_id}")
async def get_payment_status(
    order_id: str,
    db: Session = Depends(get_db)
):
    """
    Get payment status for an order
    """
    try:
        # Get payment status from database
        payment = payment_service.get_payment_by_order_id(db, order_id)
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return {
            "order_id": order_id,
            "status": payment.payment_status.value,
            "amount": payment.amount,
            "payment_method": payment.payment_method.value,
            "transaction_id": payment.transaction_id,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
            "message": "Payment status retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# API endpoints đã được đơn giản hóa và tối ưu cho MVP