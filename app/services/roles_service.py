from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.permissions import Permissions
from app.models.role import Role, UserRole
from app.schemas.roles import PermissionResponse, RoleCreate, RoleResponse


# Danh sách vai trò
def get_list_roles(db: Session):
    roles = (
        db.query(
            Role,
            func.count(UserRole.user_id).label("user_count"),
            func.count(Permissions.permission_id).label("permission_count")
        )
        .outerjoin(UserRole, Role.role_id == UserRole.role_id)
        .outerjoin(Role.permissions)
        .group_by(Role.role_id)
        .options(joinedload(Role.permissions))
        .all()
    )
    results = []
    for role, user_count, permission_count in roles:
        # Lấy danh sách permissions đã được tải sẵn
        permissions_list = [
            PermissionResponse.model_validate(p) for p in role.permissions
        ]
        
        results.append({
            "role_id": role.role_id,
            "role_name": role.role_name,
            "description": role.description,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "user_count": user_count,
            "permission_count": permission_count,
            "permissions": permissions_list
        })
    return results

def create_role(data: RoleCreate, db: Session):
    try:
        role = Role(**data.dict())
        db.add(role)
        db.commit()
        db.refresh(role)
        return RoleResponse.from_orm(role)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")


# Danh sách quyền
def get_all_permissions(db: Session):
    permissions = db.query(Permissions).all()
    return [PermissionResponse.from_orm(permission) for permission in permissions]
