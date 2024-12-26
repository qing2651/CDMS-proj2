import os
import pymysql
import random
import base64
import simplejson as json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 从环境变量获取数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', "mysql+pymysql://bookstore:HGHEnZbbzDM7nats@103.56.115.84:3306/bookstore")

class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: float
    original_price: float
    stock: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: [str]
    pictures: [bytes]

    def __init__(self):
        self.tags = []
        self.pictures = []
        self.stock = 0
        self.original_price = 0.0

class BookDB:
    def __init__(self, large: bool = False):
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self._init_test_data()

    def _init_test_data(self):
        """初始化测试数据"""
        try:
            with self.engine.connect() as conn:
                # 检查是否已有数据
                result = conn.execute(text("SELECT count(*) FROM store_books"))
                count = result.scalar()
                
                if count == 0:
                    # 先创建测试用户
                    conn.execute(
                        text("""
                            INSERT INTO users (user_id, username, password, balance)
                            VALUES ('test_user', 'test_user', 'test_password', 0.00)
                            ON DUPLICATE KEY UPDATE user_id=user_id
                        """)
                    )
                    
                    # 再创建测试商店
                    conn.execute(
                        text("""
                            INSERT INTO stores (store_id, owner_id)
                            VALUES ('test_store', 'test_user')
                            ON DUPLICATE KEY UPDATE store_id=store_id
                        """)
                    )
                    
                    # 添加测试数据到 book 表和 store_books 表
                    test_data = [
                        {
                            'id': 'test_book_1',
                            'title': '测试图书1',
                            'author': '作者1',
                            'publisher': '出版社1',
                            'price': 45.00,
                            'stock': 100
                        },
                        {
                            'id': 'test_book_2',
                            'title': '测试图书2',
                            'author': '作者2',
                            'publisher': '出版社2',
                            'price': 55.00,
                            'stock': 100
                        },
                        {
                            'id': 'test_book_3',
                            'title': '测试图书3',
                            'author': '作者3',
                            'publisher': '出版社3',
                            'price': 65.00,
                            'stock': 100
                        }
                    ]
                    
                    # 先插入数据到 book 表
                    for book in test_data:
                        conn.execute(
                            text("""
                                INSERT INTO book (
                                    id, title, author, publisher, price
                                ) VALUES (
                                    :id, :title, :author, :publisher, :price
                                )
                            """),
                            book
                        )
                    
                    # 再插入数据到 store_books 表
                    for book in test_data:
                        conn.execute(
                            text("""
                                INSERT INTO store_books (
                                    store_id, book_id, price, stock_level
                                ) VALUES (
                                    'test_store', :id, :price, :stock
                                )
                            """),
                            book
                        )
                    conn.commit()
                    print("测试数据初始化成功")
        except Exception as e:
            print(f"初始化测试数据失败: {str(e)}")
            raise

    def get_book_count(self):
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT count(*) FROM store_books"))
            return result.scalar()

    def get_book_info(self, start, size) -> [Book]:
        """获取图书信息
        Args:
            start: 起始位置（从0开始）
            size: 获取的数量
        Returns:
            包含图书信息的列表
        """
        books = []
        
        # 参数验证
        if start < 0 or size <= 0:
            return books
            
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT sb.book_id, sb.price, sb.stock_level
                        FROM store_books sb
                        ORDER BY sb.book_id 
                        LIMIT :size OFFSET :start
                    """),
                    {"size": size, "start": start}
                )
                
                for row in result:
                    book = Book()
                    book.id = row[0]
                    book.price = row[1]
                    book.stock = row[2]
                    books.append(book)
        except Exception as e:
            print(f"获取图书信息失败: {str(e)}")
            
        return books

    def init_database(self):
        """初始化数据库"""
        try:
            # 使用正确的方式注册测试用户
            from fe.access.new_buyer import register_new_buyer
            test_user = register_new_buyer("test_user", "test_password")
            return True
        except Exception as e:
            logger.error(f"初始化数据库失败: {str(e)}")
            return False
