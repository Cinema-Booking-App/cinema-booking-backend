from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.token_utils import create_token
from app.schemas.auth import EmailVerificationRequest, UserLogin, UserRegister
from app.schemas.users import UserResponse
from app.services.auth_service import get_current_user, login, register, resend_verification_code, verify_email, verify_refresh_token
from app.utils.response import success_response
router = APIRouter()

# Đăng ký tài khoản người dùng mới.
@router.post("/register")
def auth_register(user_in: UserRegister, db: Session = Depends(get_db)):
    return success_response(register(db, user_in))

# Đăng nhập tài khoản.
@router.post("/login")
def login_route(user_in: UserLogin, db: Session = Depends(get_db), request: Request = None):
    result = login(db, user_in , request)
    return success_response(result)

# Xác nhận email với mã OTP
@router.post("/verify-email")
def verify_user_email(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    return success_response(verify_email(db, request))

# Gửi lại mã xác nhận
@router.post("/resend-verification")
def resend_verification(email: str, db: Session = Depends(get_db)):
    return success_response(resend_verification_code(db, email))

# Lấy thông tin người dùng đã đăng nhập
@router.get('/me')
def get_user_info(current_user:UserResponse = Depends(get_current_user), db: Session = Depends(get_db)):
    user_dict = current_user.dict()
    # Truy vấn bảng ranks theo rank_id để lấy rank_name
    rank_name = None
    if user_dict.get("rank_id"):
        from app.models.ranks import Ranks
        rank = db.query(Ranks).filter(Ranks.rank_id == user_dict["rank_id"]).first()
        if rank:
            rank_name = rank.rank_name
    user_dict["rank_name"] = rank_name
    return success_response(user_dict)


# Logout endpoint - for stateless JWT this is a no-op, provided for frontend convenience
@router.get('/logout')
def logout_route(request: Request = None):
    """Logout endpoint: returns success so frontend can call /logout and clear client state.
    If you implement token revocation later, add logic here to blacklist the token.
    """
    return success_response({"message": "Logged out"})

@router.post("/refresh-token")
def refresh_access_token(token: str, db: Session = Depends(get_db)):
    # Xác minh refresh token
    token_data = verify_refresh_token(token, db)
    # Trả về theo format chung
    return success_response(token_data)