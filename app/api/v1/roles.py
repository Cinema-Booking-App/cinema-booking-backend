from fastapi import APIRouter, Depends
from app.core.security import get_current_active_user
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.roles import PermissionCreate, RoleCreate
from app.services.roles_service import *
from app.utils.response import success_response

router = APIRouter()


@router.get("/roles")
def get_list_role(db: Session = Depends(get_db)):
    data = success_response(get_list_roles(db))
    return data


@router.post("/roles")
def add_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    # _ = Depends(get_current_active_user)
):
    return success_response(create_role_with_permissions(data, db=db))


@router.delete("/roles/{role_id}")
def remove_role(
    role_id: int,
    db: Session = Depends(get_db),
    # _ = Depends(get_current_active_user)
):
    return success_response(delete_role(role_id, db=db))


# Permission
@router.get("/permissions")
def get_list_permissions(db: Session = Depends(get_db)):
    data = success_response(get_all_permissions(db))
    return data


@router.post("/permissions")
def add_permissions(
    data: PermissionCreate,
    db: Session = Depends(get_db),
    # _ = Depends(get_current_active_user)
):
    return success_response(create_permissions(db=db, data=data))
