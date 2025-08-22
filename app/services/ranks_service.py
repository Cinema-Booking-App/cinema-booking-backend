from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.ranks import Ranks
from app.schemas.ranks import RankCreate, RankUpdate
from sqlalchemy import desc

# Lấy tất cả ranks với phân trang và tìm kiếm
def get_all_ranks(db: Session, skip: int = 0, limit: int = 10, search_query: str = None):
    query = db.query(Ranks)
    if search_query:
        query = query.filter(Ranks.rank_name.ilike(f"%{search_query}%"))
    total = query.count()
    ranks = query.offset(skip).limit(limit).all()
    return {"items": ranks, "total": total}

# Lấy rank theo ID, có kiểm tra tồn tại 
def get_rank_by_id(db: Session, rank_id: int):
    rank = db.query(Ranks).filter(Ranks.rank_id == rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail="Xếp hạng không tìm thấy")
    return rank

# Tạo rank mới
def create_rank(db: Session, rank_data: RankCreate):
    # Kiểm tra nếu rank_name đã tồn tại
    if rank_data.is_default is None:
        raise HTTPException(status_code=400, detail="is_default phải được cung cấp (true or false)")
    if db.query(Ranks).filter(Ranks.rank_name == rank_data.rank_name).first():
        raise HTTPException(status_code=400, detail="Tên xếp hạng đã tồn tại")
    
    rank = Ranks(
        rank_name=rank_data.rank_name,
        spending_target=rank_data.spending_target,
        ticket_percent=rank_data.ticket_percent,
        combo_percent=rank_data.combo_percent,
        is_default=rank_data.is_default,
    )
    db.add(rank)
    db.commit()
    db.refresh(rank)
    return rank

# Cập nhật rank
def update_rank(db: Session, rank_id: int, rank_data: RankUpdate):
    rank = db.query(Ranks).filter(Ranks.rank_id == rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail="Xếp hạng không tìm thấy")
    
    # Cập nhật các trường nếu có
    if rank_data.rank_name is not None:
        rank.rank_name = rank_data.rank_name
    if rank_data.spending_target is not None:
        rank.spending_target = rank_data.spending_target
    if rank_data.ticket_percent is not None:
        rank.ticket_percent = rank_data.ticket_percent
    if rank_data.combo_percent is not None:
        rank.combo_percent = rank_data.combo_percent
    if rank_data.is_default is not None:
        rank.is_default = rank_data.is_default
    
    db.commit()
    db.refresh(rank)
    return rank

# Xoá rank
def delete_rank(db: Session, rank_id: int):
    rank = db.query(Ranks).filter(Ranks.rank_id == rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail="Xếp hạng không tìm thấy")
    
    db.delete(rank)
    db.commit()
    return {"detail": "Rank deleted successfully"}