from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.token_utils import create_token
from app.models.email_verifications import EmailVerification
from app.models.users import Users, UserStatusEnum

# Thêm import cho model Role và UserRole
from app.models.roles import Roles, UserRole
from app.schemas.auth import EmailVerificationRequest, UserLogin, UserRegister
from app.schemas.users import UserResponse
from app.services.email_service import EmailService
from app.services.users_service import pwd_context
from fastapi.security import HTTPBearer, OAuth2PasswordBearer

# --- Khởi tạo dịch vụ email và OAuth2 scheme ---
# Khởi tạo EmailService với các thông tin cấu hình từ settings
email_service = EmailService(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username=settings.EMAIL_USERNAME,
    password=settings.EMAIL_PASSWORD,
)


# Khai báo OAuth2 scheme cho việc lấy token từ header
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")
security_scheme = HTTPBearer()

def create_access_token(data: dict) -> str:
    """Tạo token truy cập (access token)."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(data, access_token_expires, "access")


def create_refresh_token(data: dict) -> str:
    """Tạo token làm mới (refresh token)."""
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(data, refresh_token_expires, "refresh")


# --- Hàm xác thực người dùng hiện tại ---
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(security_scheme)
) -> Users:
    """Dependency injection để lấy người dùng hiện tại từ access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != "access":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(Users).filter(Users.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại"
        )
    return user


# --- Hàm logic cho các chức năng ---
def register(db: Session, user_in: UserRegister):
    """Xử lý logic đăng ký người dùng mới."""
    existing_user = db.query(Users).filter(Users.email == user_in.email).first()

    if existing_user:
        if existing_user.status == UserStatusEnum.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được đăng ký"
            )
        else:
            # Nếu user đã tồn tại nhưng chưa active, hướng dẫn họ gửi lại mã
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản đã tồn tại nhưng chưa được kích hoạt. Vui lòng kiểm tra email hoặc yêu cầu gửi lại mã.",
            )

    try:
        hashed_password = pwd_context.hash(user_in.password)
        new_user = Users(
            full_name=user_in.full_name,
            email=user_in.email,
            password_hash=hashed_password,
            status=UserStatusEnum.pending,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Tạo mã xác nhận và gửi email
        verification_code = email_service.generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        verification = EmailVerification(
            email=user_in.email,
            verification_code=verification_code,
            expires_at=expires_at,
        )
        db.add(verification)

        # Thêm logic gán role mặc định cho người dùng mới
        # Tìm role 'user' trong database. Nếu không tồn tại thì raise lỗi
        default_role = db.query(Roles).filter(Roles.role_name == "user").first()
        if not default_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vai trò mặc định 'user' không tồn tại trong hệ thống.",
            )

        # Tạo bản ghi UserRole để gán vai trò cho người dùng
        new_user_role = UserRole(user_id=new_user.user_id, role_id=default_role.role_id)
        db.add(new_user_role)

        db.commit()

        # Sau khi commit, gửi email
        if not email_service.send_verification_email(user_in.email, verification_code):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể gửi email xác nhận. Vui lòng thử lại sau.",
            )

        return {
            "message": "Đăng ký thành công! Vui lòng kiểm tra email để xác minh tài khoản.",
            "email": user_in.email,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Có lỗi xảy ra trong quá trình đăng ký: {str(e)}",
        )


def login(db: Session, user_in: UserLogin):
    """Xử lý logic đăng nhập."""
    user = db.query(Users).filter(Users.email == user_in.email).first()

    if not user or not pwd_context.verify(
        user_in.password, getattr(user, "password_hash", "")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không trùng khớp",
        )

    if user.status != UserStatusEnum.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa được xác minh. Vui lòng kiểm tra email để kích hoạt.",
        )
    # Lấy vai trò của người dùng và thêm vào payload token
    user_roles_db = (
        db.query(Roles.role_name)
        .join(UserRole)
        .filter(UserRole.user_id == user.user_id)
        .all()
    )
    roles_list = [role_name[0] for role_name in user_roles_db]

    # Tạo payload cho token
    payload = {"sub": user.email, "roles": roles_list}

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token({"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "roles": roles_list,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user),
    }


def verify_refresh_token(token: str, db: Session) -> dict:
    """Xác minh refresh token và tạo access token mới."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Mã làm mới không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != "refresh":
            raise credentials_exception

        user = db.query(Users).filter(Users.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng",
            )

        # Tạo access token mới
        new_access_token = create_access_token({"sub": user.email})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise credentials_exception


def verify_email(db: Session, request: EmailVerificationRequest):
    """Xác nhận email bằng mã OTP."""
    try:
        verification = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.email == request.email,
                EmailVerification.verification_code == request.verification_code,
                EmailVerification.is_used == False,
            )
            .first()
        )

        if not verification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã xác nhận không hợp lệ hoặc đã được sử dụng.",
            )

        if datetime.now(timezone.utc) > verification.expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã xác nhận đã hết hạn.",
            )

        user = db.query(Users).filter(Users.email == request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng.",
            )

        user.status = UserStatusEnum.active
        verification.is_used = True

        db.commit()
        db.refresh(user)

        access_token = create_access_token({"sub": user.email})
        refresh_token = create_refresh_token({"sub": user.email})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Có lỗi xảy ra trong quá trình xác minh: {str(e)}",
        )


def resend_verification_code(db: Session, email: str):
    """Gửi lại mã xác nhận cho người dùng chưa kích hoạt."""
    try:
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Người dùng không tồn tại.",
            )

        if user.status == UserStatusEnum.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản đã được xác nhận.",
            )

        # Đánh dấu các mã xác nhận cũ là đã sử dụng
        db.query(EmailVerification).filter(
            EmailVerification.email == email, EmailVerification.is_used == False
        ).update({"is_used": True})

        # Tạo và lưu mã mới
        verification_code = email_service.generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        verification = EmailVerification(
            email=email, verification_code=verification_code, expires_at=expires_at
        )
        db.add(verification)
        db.commit()

        # Gửi email xác nhận
        if not email_service.send_verification_email(email, verification_code):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể gửi email xác nhận. Vui lòng thử lại.",
            )

        return {"message": "Mã xác nhận đã được gửi lại thành công."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Có lỗi xảy ra: {str(e)}",
        )
