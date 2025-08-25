from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date
from app.models.promotions import Promotions
from app.schemas.promotions import PromotionCreate, PromotionUpdate

def get_all_promotions(db: Session):
    return db.query(Promotions).all()

def get_promotion_by_id(db: Session, promotion_id: int):
    promotion = db.query(Promotions).filter(Promotions.promotion_id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promotion

def create_promotion(db: Session, promotion_in: PromotionCreate):
    # Check if code already exists
    existing_promotion = db.query(Promotions).filter(Promotions.code == promotion_in.code).first()
    if existing_promotion:
        raise HTTPException(status_code=400, detail="Promotion code already exists")
    
    db_promotion = Promotions(**promotion_in.dict())
    db.add(db_promotion)
    db.commit()
    db.refresh(db_promotion)
    return db_promotion

def update_promotion(db: Session, promotion_id: int, promotion_in: PromotionUpdate):
    promotion = db.query(Promotions).filter(Promotions.promotion_id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    # Check if code already exists (if updating code)
    if promotion_in.code and promotion_in.code != promotion.code:
        existing_promotion = db.query(Promotions).filter(Promotions.code == promotion_in.code).first()
        if existing_promotion:
            raise HTTPException(status_code=400, detail="Promotion code already exists")
    
    for key, value in promotion_in.dict(exclude_unset=True).items():
        setattr(promotion, key, value)
    
    db.commit()
    db.refresh(promotion)
    return promotion

def delete_promotion(db: Session, promotion_id: int):
    promotion = db.query(Promotions).filter(Promotions.promotion_id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    db.delete(promotion)
    db.commit()
    return {"message": "Promotion deleted successfully"}

def toggle_promotion_status(db: Session, promotion_id: int, is_active: bool):
    promotion = db.query(Promotions).filter(Promotions.promotion_id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    promotion.is_active = is_active
    db.commit()
    db.refresh(promotion)
    return promotion

def get_active_promotions(db: Session):
    """Get all active promotions that are within their valid date range"""
    today = date.today()
    promotions = db.query(Promotions).filter(
        and_(
            Promotions.is_active == True,
            Promotions.start_date <= today,
            Promotions.end_date >= today
        )
    ).all()
    
    return promotions

def validate_promotion_code(db: Session, code: str, promotion_id: int = None):
    """Validate if promotion code is available"""
    query = db.query(Promotions).filter(Promotions.code == code)
    if promotion_id:
        query = query.filter(Promotions.promotion_id != promotion_id)
    
    existing = query.first()
    if existing:
        raise HTTPException(status_code=400, detail="Promotion code already exists")
    return True 