from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.combos_service import (
    create_combo,
    get_all_combos,
    get_combo_by_id,
    update_combo,
    delete_combo,
    create_dish
)
from app.schemas.combos import ComboCreate, ComboUpdate, DishCreate
from app.utils.response import success_response

router = APIRouter()

# Tạo món ăn mới
@router.post("/dishes")
def add_dish(dish_in: DishCreate, db: Session = Depends(get_db)):
    return success_response(create_dish(db, dish_in))

# Lấy tất cả combo
@router.get("/combos")
def list_combos(db: Session = Depends(get_db)):
    return success_response(get_all_combos(db))

# Lấy chi tiết combo theo ID
@router.get("/combos/{combo_id}")
def detail_combo(combo_id: int, db: Session = Depends(get_db)):
    return success_response(get_combo_by_id(db, combo_id))

# Tạo combo mới
@router.post("/combos")
def add_combo(combo_in: ComboCreate, db: Session = Depends(get_db)):
    return success_response(create_combo(db, combo_in))

# Cập nhật combo theo ID
@router.put("/combos/{combo_id}")
def edit_combo(combo_id: int, combo_in: ComboUpdate, db: Session = Depends(get_db)):
    return success_response(update_combo(db, combo_id, combo_in))

# Xoá combo theo ID
@router.delete("/combos/{combo_id}")
def remove_combo(combo_id: int, db: Session = Depends(get_db)):
    return success_response(delete_combo(db, combo_id))