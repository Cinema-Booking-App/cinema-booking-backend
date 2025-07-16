from app.core.database import engine

if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            print("Kết nối database thành công!")
    except Exception as e:
        print("Kết nối database thất bại:", e) 

# python -m app.tests.test_db_connection