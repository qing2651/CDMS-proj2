from db_config import init_db
from store import User, Store, Book, BookImage, StoreBook, Order, OrderItem

def test_database_connection():
    try:
        init_db()
        print("数据库连接测试成功！")
    except Exception as e:
        print(f"数据库连接测试失败：{str(e)}")

if __name__ == "__main__":
    test_database_connection() 