from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = ""
    SECRET_KEY: str  = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int  = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int  = 7
    ALGORITHM: str  = "HS256"
    EMAIL_USERNAME: str = "tran26122003@gmail.com"
    EMAIL_PASSWORD: str = "kaxq pvyc rtaz qcon"
    class Config:
        env_file = ".env"

settings = Settings() 