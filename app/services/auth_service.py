from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException,status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.email_verifications import EmailVerification
from app.models.users import Users, UserStatusEnum ,UserRoleEnum
from app.schemas.auth import EmailVerificationRequest, UserLogin, UserRegister
from app.schemas.users import  UserResponse
from app.services.email_service import EmailService
from app.services.users_service import pwd_context
from fastapi.security import OAuth2PasswordBearer

email_service = EmailService(
    smtp_server="smtp.gmail.com", 
    smtp_port=587,
    username=settings.EMAIL_USERNAME, 
    password=settings.EMAIL_PASSWORD,
    
)

def register(db: Session, user_in : UserRegister):
    try:
        # Kiểm tra xem email đã tồn tại chưa
        existing_user = db.query(Users).filter(Users.email == user_in.email).first()
        if existing_user:
            if existing_user.status == UserStatusEnum.active:   
                raise HTTPException(status_code=400, detail="Email existing ")
            else:
                # Xóa mã xác nhận cũ cho user này
                db.query(EmailVerification).filter(
                    EmailVerification.email == user_in.email,
                    EmailVerification.is_used == False,
                ).delete()
                # Tạo mã xác nhận mới
                verification_code = email_service.generate_verification_code()
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=10) # Đảm bảo dùng aware datetime

                verification = EmailVerification(
                    email = user_in.email,
                    verification_code = verification_code,
                    expires_at = expires_at
                )
                db.add(verification)
                db.commit()
                db.refresh(existing_user) 

                # Gửi lại email xác nhận
                if not email_service.send_verification_email(user_in.email, verification_code):
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR , detail="Not send email")
                return {
                    "message": "Registration successful! Please check your email to confirm your account.",
                    "email": user_in.email
                }
        
        hashed_password = pwd_context.hash(user_in.password)
        user = Users(
            full_name=user_in.full_name,
            email=user_in.email,
            password_hash=hashed_password,
            status= UserStatusEnum.pending,
            role = UserRoleEnum.customer,
        )
        db.add(user)

       
        # Xóa mã xác nhận cũ 
        db.query(EmailVerification).filter(
            EmailVerification.email == user_in.email,
            EmailVerification.is_used == False,
        ).delete()
         #Tạo mã xác nhập 
        verification_code = email_service.generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        verification = EmailVerification(
            email = user_in.email,
            verification_code = verification_code,
            expires_at = expires_at
        )
        db.add(verification)
        db.commit()
        db.refresh(user)
        if not email_service.send_verification_email(user_in.email, verification_code):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR , detail="Not send email")
        return {
            "message": "Registration successful! Please check your email to confirm your account.",
            "email": user_in.email
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f" {str(e)}"
        ) 
def login(db: Session, user_in: UserLogin):
    user = db.query(Users).filter(Users.email == user_in.email).first()
    if not user or not pwd_context.verify(user_in.password, getattr(user, "password_hash", None)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu không trùng khớp")
    if user.status != UserStatusEnum.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verify")

    access_token = create_access_token({"sub": user.email, "role": str(user.role)})
    refresh_token = create_access_token({"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

# Làm mới token
def verify_refresh_token(token: str, db: Session) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mã làm mới không hợp lệ",
            )
        
        user = db.query(Users).filter(Users.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy người dùng ",
            )
        
        return {"sub": email, "role": str(user.role)}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không thể xác thực mã làm mới",
        )

# Khai báo OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# Lấy thông tin người dùng đang đăng nhập
def get_current_user(db:Session = Depends(get_db) ,token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])
        email:str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "access":
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Không thể xác thực thông tin đăng nhập"
        ) 
        user = db.query(Users).filter(Users.email==email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng")
        return UserResponse.from_orm(user)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Không thể xác thực thông tin đăng nhập"
        ) 

# Xác nhận email với mã OTP
def verify_email(db: Session, request: EmailVerificationRequest):
    try:
        # Tìm mã xác nhận
        verification = db.query(EmailVerification).filter(
            EmailVerification.email == request.email,
            EmailVerification.verification_code == request.verification_code,
            EmailVerification.is_used == False
        ).first()
        
        if not verification:
            raise HTTPException(status_code=400, detail="The verification code is invalid.")
        
        # Kiểm tra hết hạn
        if datetime.now(timezone.utc) > verification.expires_at:
            raise HTTPException(status_code=400, detail="The verification code has expired.")
        
        # Tìm user và cập nhật status
        user = db.query(Users).filter(Users.email == request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Cập nhật user status và đánh dấu mã đã sử dụng
        user.status = UserStatusEnum.active
        verification.is_used = True
        
        db.commit()
        db.refresh(user)
        access_token = create_access_token({"sub": user.email, "role": str(user.role)})
        refresh_token = create_access_token({"sub": user.email})

        return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

def resend_verification_code(db: Session, email: str):
    """Gửi lại mã xác nhận"""
    try:
        # Kiểm tra user tồn tại và chưa xác nhận
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.status == UserStatusEnum.active:
            raise HTTPException(status_code=400, detail="Tài khoản đã được xác nhận")
        
        # Xóa mã cũ
        db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.is_used == False
        ).delete()
        
        # Tạo mã mới
        verification_code = email_service.generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        verification = EmailVerification(
            email=email,
            verification_code=verification_code,
            expires_at=expires_at
        )
        db.add(verification)
        db.commit()
        
        # Gửi email
        if not email_service.send_verification_email(email, verification_code):
            raise HTTPException(status_code=500, detail="Email not send")
        
        return {"message": "The confirmation code has been resent."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))