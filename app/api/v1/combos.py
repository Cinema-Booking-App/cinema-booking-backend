from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.services.combos_service import (
    create_combo,
    get_all_combos,
    get_combo_by_id,
    update_combo,
    delete_combo,
    create_dish
)
from app.schemas.combos import ComboCreate, ComboUpdate, ComboResponse, DishCreate, DishResponse

router = APIRouter()

# Tạo món ăn mới
@router.post("/dishes", response_model=DishResponse)
def add_dish(dish_in: DishCreate, db: Session = Depends(get_db)):
    return create_dish(db, dish_in)

# Lấy tất cả combo
@router.get("/combos", response_model=List[ComboResponse])
def list_combos(db: Session = Depends(get_db)):
    return get_all_combos(db)

# Lấy chi tiết combo theo ID
@router.get("/combos/{combo_id}", response_model=ComboResponse)
def detail_combo(combo_id: int, db: Session = Depends(get_db)):
    return get_combo_by_id(db, combo_id)

# Tạo combo mới
@router.post("/combos", response_model=ComboResponse)
def add_combo(combo_in: ComboCreate, db: Session = Depends(get_db)):
    return create_combo(db, combo_in)

# Cập nhật combo theo ID
@router.put("/combos/{combo_id}", response_model=ComboResponse)
def edit_combo(combo_id: int, combo_in: ComboUpdate, db: Session = Depends(get_db)):
    return update_combo(db, combo_id, combo_in)

# Xoá combo theo ID
@router.delete("/combos/{combo_id}", response_model=bool)
def remove_combo(combo_id: int, db: Session = Depends(get_db)):
    return delete_combo(db, combo_id)