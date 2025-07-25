from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# Tạo engine kết nối tới database
engine = create_engine(settings.DATABASE_URL)
# Tạo class SessionLocal để tạo các phiên làm việc với database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Tạo class Base để các model ORM kế thừa
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test in test_db_connection.py