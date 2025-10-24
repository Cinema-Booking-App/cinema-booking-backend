from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:12345678@localhost:5432/cinema-booking"
    SECRET_KEY: str  = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int  
    REFRESH_TOKEN_EXPIRE_DAYS: int 
    ALGORITHM: str  = "HS256"
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    
    # SMTP / Email server settings
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_SENDER_NAME: str = "CinePlus"
    CORS_ALLOW_ORIGINS: str = ""  # Comma-separated list of origins
    
    # VNPay Configuration
    VNPAY_TMN_CODE: str = ""  # Website ID in VNPAY System
    VNPAY_HASH_SECRET_KEY: str = ""  # Secret key for create checksum
    VNPAY_PAYMENT_URL: str = ""  # VNPay payment gateway URL
    VNPAY_API_URL: str = ""  # VNPay API URL for queries
    VNPAY_RETURN_URL: str = ""  # Backend return URL
    VNPAY_IPN_URL: str = ""  # Backend IPN URL
    
    class Config:
        env_file = ".env"

settings = Settings() 