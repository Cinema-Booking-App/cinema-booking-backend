from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.ranks import RankCreate, RankUpdate, RankResponse
from app.services.ranks_service import *
from app.core.database import get_db
from app.utils.response import success_response

router = APIRouter()
# ==================== RANKS ROUTES ====================
@router.get("/ranks")
def list_ranks(skip: int = 0, limit: int = 10, search_query: Optional[str] = None, db: Session = Depends(get_db)):
    return success_response(get_all_ranks(db, skip, limit, search_query))

@router.get("/ranks/{rank_id}")
def detail_rank(rank_id: int, db: Session = Depends(get_db)):
    return success_response(get_rank_by_id(db, rank_id))

@router.post("/ranks")
def create_new_rank(rank_in: RankCreate, db: Session = Depends(get_db)):
    return success_response(create_rank(db, rank_in))

@router.put("/ranks/{rank_id}")
def update_existing_rank(rank_id: int, rank_in: RankUpdate, db: Session = Depends(get_db)):
    return success_response(update_rank(db, rank_id, rank_in))

@router.delete("/ranks/{rank_id}")
def delete_rank(rank_id: int, db: Session = Depends(get_db)):
    rank = get_rank_by_id(db, rank_id)
    db.delete(rank)
    db.commit()
    return success_response({"detail": "Xếp hạng đã được xóa thành công"})