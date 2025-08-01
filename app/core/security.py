from fastapi import Depends, HTTPException, status
from app.models.users import UserStatusEnum, Users
from app.services.auth_service import get_current_user

# Hàm get_current_active_user vẫn ở đây
def get_current_active_user(current_user: Users = Depends(get_current_user)):
    """Lấy người dùng hiện tại chỉ khi họ đã được kích hoạt."""
    if current_user.status != UserStatusEnum.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản chưa được xác minh"
        )
    return current_user
