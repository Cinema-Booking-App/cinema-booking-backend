from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.schemas.common import PaginatedResponse
from app.models.combos import Combo, ComboDish, ComboItem
from app.schemas.combos import ComboCreate, ComboUpdate, ComboDishCreate, ComboDishUpdate
from sqlalchemy import desc

# ==================== COMBO CRUD ====================
# Lấy tất cả combo kèm theo combo_items
def get_all_combos(db: Session, skip: int = 0, limit: int = 10, search_query: str = None):
    query = db.query(Combo).options(joinedload(Combo.combo_items).joinedload(ComboItem.dish)).order_by(desc(Combo.combo_id))
    if search_query:
        query = query.filter(Combo.combo_name.ilike(f"%{search_query}%"))
    total = query.count()
    combos = query.offset(skip).limit(limit).all()
    for combo in combos:
        combo.combo_items  # load lazy
    return {"items": combos, "total": total}

# Lấy combo theo ID, có kiểm tra tồn tại và load combo_items
def get_combo_by_id(db: Session, combo_id: int):
    combo = db.query(Combo).options(joinedload(Combo.combo_items).joinedload(ComboItem.dish)).filter(Combo.combo_id == combo_id).first()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo not found")
    combo.combo_items  # load lazy
    return combo

# Tạo combo và danh sách combo_items đi kèm
def create_combo(db: Session, combo_data: ComboCreate):
    # Tạo combo chính
    for item in combo_data.items:
        if not db.query(ComboDish).filter(ComboDish.dish_id == item.dish_id).first():
            raise HTTPException(status_code=404, detail=f"Dish with id {item.dish_id} not found")
    
    combo = Combo(
        combo_name=combo_data.combo_name,
        description=combo_data.description,
        price=combo_data.price,
        image_url=combo_data.image_url,
        status=combo_data.status,
    )
    db.add(combo)
    db.commit()
    db.refresh(combo)

    # Thêm combo_items
    for item in combo_data.items:
        combo_item = ComboItem(
            combo_id=combo.combo_id,
            dish_id=item.dish_id,
            quantity=item.quantity,
        )
        db.add(combo_item)
    db.commit()
    db.refresh(combo)
    return combo

# Cập nhật combo và cập nhật danh sách combo_items nếu có
def update_combo(db: Session, combo_id: int, combo_data: ComboUpdate):
    combo = get_combo_by_id(db, combo_id)

    # Cập nhật các trường combo
    if combo_data.items is not None:
        for item in combo_data.items:
            if not db.query(ComboDish).filter(ComboDish.dish_id == item.dish_id).first():
                raise HTTPException(status_code=404, detail=f"Dish with id {item.dish_id} not found")

    for field, value in combo_data.dict(exclude_unset=True, exclude={"items"}).items():
        setattr(combo, field, value)
    db.commit()

    # Nếu có cập nhật danh sách items → xóa hết và thêm lại
    if combo_data.items is not None:
        db.query(ComboItem).filter(ComboItem.combo_id == combo_id).delete()
        for item in combo_data.items:
            combo_item = ComboItem(
                combo_id=combo.combo_id,
                dish_id=item.dish_id,
                quantity=item.quantity,
            )
            db.add(combo_item)
        db.commit()

    db.refresh(combo)
    return combo

# Xóa combo và các combo_items liên quan
def delete_combo(db: Session, combo_id: int):
    combo = get_combo_by_id(db, combo_id)

    # Xóa combo_items trước
    db.query(ComboItem).filter(ComboItem.combo_id == combo_id).delete()
    db.delete(combo)
    db.commit()

    return {"message": "Combo deleted successfully"}


# ==================== DISH CRUD ====================
def get_all_dishes(db: Session):
    return db.query(ComboDish).all()

def get_dish_by_id(db: Session, dish_id: int):
    dish = db.query(ComboDish).filter(ComboDish.dish_id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    return dish

def create_dish(db: Session, dish_data: ComboDishCreate):
    dish = ComboDish(**dish_data.dict())
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish

def update_dish(db: Session, dish_id: int, dish_data: ComboDishUpdate):
    dish = get_dish_by_id(db, dish_id)
    for field, value in dish_data.dict(exclude_unset=True).items():
        setattr(dish, field, value)
    db.commit()
    db.refresh(dish)
    return dish

def delete_dish(db: Session, dish_id: int):
    dish = get_dish_by_id(db, dish_id)
    db.delete(dish)
    db.commit()
    return {"message": "Dish deleted successfully"}


