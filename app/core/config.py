from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:12345678@localhost:5432/cinema-booking"
    SECRET_KEY: str  = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int  = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int  = 7
    ALGORITHM: str  = "HS256"
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    CORS_ALLOW_ORIGINS: str = ""  # Comma-separated list of origins
    class Config:
        env_file = ".env"

settings = Settings() 