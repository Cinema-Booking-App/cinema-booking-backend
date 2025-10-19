from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.payments_service import PaymentService
from app.schemas.payments import PaymentRequest
from app.utils.response import success_response
from app.core.security import get_current_active_user
from app.models.users import Users
router = APIRouter()
payment_service = PaymentService()

# Tạo thanh toán
@router.post("/create")
async def create_vnpay_payment(
    payment_request: PaymentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_active_user),
):
    try:
        client_ip = request.client.host
        payment = payment_service.create_payment(db, payment_request, client_ip, user_id=current_user.user_id)
        return success_response(payment)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {e}")


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
        payment_result = payment_service.handle_vnpay_callback(db, query_params)

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