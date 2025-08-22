from fastapi import APIRouter, Depends
from app.core.security import get_current_active_user
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.roles import RoleCreate
from app.services.roles_service import create_role, get_all_roles
from app.utils.response import success_response

router = APIRouter()


@router.get("/roles")
def get_list_role(db: Session = Depends(get_db)):
    data = success_response(get_all_roles(db))
    return data


@router.post("/roles")
def add_role(data: RoleCreate, db: Session = Depends(get_db), _ = Depends(get_current_active_user)):
    return success_response(create_role(data, db=db))
