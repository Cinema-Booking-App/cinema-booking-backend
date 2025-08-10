from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.combos import ComboCreate, ComboUpdate, ComboDishCreate, ComboDishUpdate

from app.services.combos_service import *
from app.core.database import get_db
from app.utils.response import success_response

router = APIRouter()


# ==================== COMBO ROUTES ====================

@router.get("/combos")
def list_combos(skip: int = 0, limit: int = 10, search_query: Optional[str] = None, db: Session = Depends(get_db)):
    return success_response(get_all_combos(db, skip, limit, search_query))


@router.get("/combos/{combo_id}")
def detail_combo(combo_id: int, db: Session = Depends(get_db)):
    return success_response(get_combo_by_id(db, combo_id))


@router.post("/combos")
def create_new_combo(combo_in: ComboCreate, db: Session = Depends(get_db)):
    return success_response(create_combo(db, combo_in))


@router.put("/combos/{combo_id}")
def update_existing_combo(combo_id: int, combo_in: ComboUpdate, db: Session = Depends(get_db)):
    return success_response(update_combo(db, combo_id, combo_in))


@router.delete("/combos/{combo_id}")
def delete_combo_by_id(combo_id: int, db: Session = Depends(get_db)):
    return success_response(delete_combo(db, combo_id))


# ==================== DISH ROUTES ====================

@router.get("/dishes")
def list_dishes(db: Session = Depends(get_db)):
    return success_response(get_all_dishes(db))


@router.get("/dishes/{dish_id}")
def detail_dish(dish_id: int, db: Session = Depends(get_db)):
    return success_response(get_dish_by_id(db, dish_id))


@router.post("/dishes")
def create_new_dish(dish_in: ComboDishCreate, db: Session = Depends(get_db)):
    return success_response(create_dish(db, dish_in))


@router.put("/dishes/{dish_id}")
def update_existing_dish(dish_id: int, dish_in: ComboDishUpdate, db: Session = Depends(get_db)):
    return success_response(update_dish(db, dish_id, dish_in))


@router.delete("/dishes/{dish_id}")
def delete_dish_by_id(dish_id: int, db: Session = Depends(get_db)):
    return success_response(delete_dish(db, dish_id))

