from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class RoleBase(BaseModel):
    role_name: str
    description: str


class RoleCreate(RoleBase):
    permission_ids: List[int]


class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    description: Optional[str] = None


"""Permission Schemas"""


class PermissionBase(BaseModel):
    permission_name: str
    description: Optional[str] = None
    module: Optional[str] = None
    actions: Optional[List[str]] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    permission_name: Optional[str] = None
    description: Optional[str] = None
    module: Optional[str] = None
    actions: Optional[List[str]] = None


class PermissionResponse(PermissionBase):
    permission_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleResponse(RoleBase):
    role_id: int
    created_at: datetime
    updated_at: datetime
    permissions: Optional[List[PermissionResponse]] = None

    class Config:
        from_attributes = True
