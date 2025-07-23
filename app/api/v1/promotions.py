from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.promotions import PromotionCreate, PromotionUpdate, PromotionResponse
from app.services.promotions_service import (
    get_all_promotions, get_promotion_by_id, create_promotion, update_promotion, delete_promotion
)
from app.utils.response import success_response

router = APIRouter()

@router.get("/promotions", response_model=list[PromotionResponse])
def list_promotions(db: Session = Depends(get_db)):
    return get_all_promotions(db)

@router.get("/promotions/{promotion_id}", response_model=PromotionResponse)
def get_promotion(promotion_id: int, db: Session = Depends(get_db)):
    return get_promotion_by_id(db, promotion_id)

@router.post("/promotions", response_model=PromotionResponse, status_code=201)
def create_new_promotion(promotion_in: PromotionCreate, db: Session = Depends(get_db)):
    return create_promotion(db, promotion_in)

@router.put("/promotions/{promotion_id}", response_model=PromotionResponse)
def update_existing_promotion(promotion_id: int, promotion_in: PromotionUpdate, db: Session = Depends(get_db)):
    return update_promotion(db, promotion_id, promotion_in)

@router.delete("/promotions/{promotion_id}")
def delete_existing_promotion(promotion_id: int, db: Session = Depends(get_db)):
    return delete_promotion(db, promotion_id) 