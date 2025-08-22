from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.permissions import Permissions
from app.models.roles import Roles
from app.schemas.roles import PermissionResponse, RoleCreate, RoleResponse


# Danh sách vai trò 
def get_all_roles(db:Session):
    roles = db.query(Roles).all()
    return [RoleResponse.from_orm(role) for role in roles]

def create_role(data: RoleCreate, db: Session):
    try:
        role = Roles(**data.dict())
        db.add(role)
        db.commit()
        db.refresh(role)
        return RoleResponse.from_orm(role)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")

# Danh sách quyền 
def get_all_permissions(db:Session):
    permissions = db.query(Permissions).all()
    return [PermissionResponse.from_orm(permission) for permission in permissions]
