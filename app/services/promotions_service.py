from fastapi import HTTPException
from sqlalchemy.orm import Session
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
    db_promotion = Promotions(**promotion_in.dict())
    db.add(db_promotion)
    db.commit()
    db.refresh(db_promotion)
    return db_promotion

def update_promotion(db: Session, promotion_id: int, promotion_in: PromotionUpdate):
    promotion = db.query(Promotions).filter(Promotions.promotion_id == promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
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