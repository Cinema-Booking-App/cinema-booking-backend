from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.promotions import PromotionCreate, PromotionUpdate, PromotionResponse, PromotionStatusUpdate
from app.services.promotions_service import (
    get_all_promotions, get_promotion_by_id, create_promotion, update_promotion, delete_promotion,
    toggle_promotion_status, get_active_promotions
)
from app.utils.response import success_response

router = APIRouter()

@router.get("/promotions")
def list_promotions(db: Session = Depends(get_db)):
    """Get all promotions with computed status"""
    promotions =  get_all_promotions(db)
    return success_response(promotions)

@router.get("/promotions/active")
def list_active_promotions(db: Session = Depends(get_db)):
    """Get only active promotions that are within their valid date range"""
    return get_active_promotions(db)

@router.get("/promotions/{promotion_id}")
def get_promotion(promotion_id: int, db: Session = Depends(get_db)):
    """Get a specific promotion by ID"""
    return get_promotion_by_id(db, promotion_id)

@router.post("/promotions", response_model=PromotionResponse, status_code=201)
def create_new_promotion(promotion_in: PromotionCreate, db: Session = Depends(get_db)):
    """Create a new promotion"""
    return create_promotion(db, promotion_in)

@router.put("/promotions/{promotion_id}", response_model=PromotionResponse)
def update_existing_promotion(promotion_id: int, promotion_in: PromotionUpdate, db: Session = Depends(get_db)):
    """Update an existing promotion"""
    return update_promotion(db, promotion_id, promotion_in)

@router.patch("/promotions/{promotion_id}/status", response_model=PromotionResponse)
def update_promotion_status(promotion_id: int, status_update: PromotionStatusUpdate, db: Session = Depends(get_db)):
    """Toggle promotion active/inactive status"""
    return toggle_promotion_status(db, promotion_id, status_update.is_active)

@router.delete("/promotions/{promotion_id}")
def delete_existing_promotion(promotion_id: int, db: Session = Depends(get_db)):
    """Delete a promotion"""
    result = delete_promotion(db, promotion_id)
    return success_response(data=result, message="Promotion deleted successfully") 