from sqlalchemy import Column, String, Integer, Float, Text, TIMESTAMP, ForeignKey, DECIMAL, LargeBinary, Index, text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint, ForeignKeyConstraint
from datetime import datetime
import logging

from .db_config import Base, engine, SessionLocal

logger = logging.getLogger(__name__)

def get_db_conn():
    """获取数据库连接"""
    return SessionLocal()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(String(255), primary_key=True)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    balance = Column(DECIMAL(10, 2), nullable=False, server_default=text("1000000.00"))
    token = Column(Text, nullable=True)
    terminal = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    
    # 索引
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_token', 'token', mysql_length=255)
    )
    
    # 关系
    stores = relationship('Store', back_populates='owner', cascade='all, delete-orphan')
    orders = relationship('Order', back_populates='user', cascade='all, delete-orphan')

class Store(Base):
    __tablename__ = 'stores'
    
    store_id = Column(String(255), primary_key=True)
    owner_id = Column(String(255), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    
    # 关系
    owner = relationship('User', back_populates='stores')
    store_books = relationship('StoreBook', back_populates='store', cascade='all, delete-orphan')
    orders = relationship('Order', back_populates='store', cascade='all, delete-orphan')

class BaseBook(Base):
    __tablename__ = 'book'
    
    id = Column(String(255), primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255))
    publisher = Column(String(255))
    original_title = Column(Text)
    translator = Column(String(255))
    pub_year = Column(String(20))
    pages = Column(Integer)
    price = Column(DECIMAL(10, 2))
    currency_unit = Column(String(20))
    binding = Column(String(100))
    isbn = Column(String(20))
    author_intro = Column(Text)
    book_intro = Column(Text)
    content = Column(Text)
    tags = Column(Text)
    picture = Column(LargeBinary(length=(2**32)-1))
    
    # 索引
    __table_args__ = (
        Index('idx_book_isbn', 'isbn'),
        Index('idx_book_title', 'title')
    )
    
    # 关系
    store_books = relationship('StoreBook', back_populates='book', cascade='all, delete-orphan')
    book_images = relationship('BookImage', back_populates='base_book', cascade='all, delete-orphan')

class StoreBook(Base):
    __tablename__ = 'store_books'
    
    store_id = Column(String(255), ForeignKey('stores.store_id', ondelete='CASCADE'), primary_key=True)
    book_id = Column(String(255), ForeignKey('book.id', ondelete='CASCADE'), primary_key=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    stock_level = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # 添加唯一键约束
    __table_args__ = (
        Index('idx_store_book', 'store_id', 'book_id', unique=True),
    )
    
    # 关系
    store = relationship('Store', back_populates='store_books')
    book = relationship('BaseBook', back_populates='store_books')
    order_items = relationship('OrderItem', back_populates='store_book', cascade='all, delete-orphan')

class Order(Base):
    __tablename__ = 'orders'
    
    order_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    store_id = Column(String(255), ForeignKey('stores.store_id', ondelete='CASCADE'), nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default='pending')
    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    payment_time = Column(TIMESTAMP)
    delivery_time = Column(TIMESTAMP)
    receive_time = Column(TIMESTAMP)
    expire_time = Column(TIMESTAMP)
    
    # 关系
    user = relationship('User', back_populates='orders')
    store = relationship('Store', back_populates='orders')
    order_items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    order_id = Column(String(255), ForeignKey('orders.order_id', ondelete='CASCADE'), primary_key=True)
    book_id = Column(String(255), primary_key=True)
    store_id = Column(String(255), primary_key=True)
    count = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    
    # 添加复合外键约束
    __table_args__ = (
        UniqueConstraint('order_id', 'book_id', 'store_id', name='uq_order_item'),
        ForeignKeyConstraint(
            ['store_id', 'book_id'],
            ['store_books.store_id', 'store_books.book_id'],
            name='fk_order_items_store_book',
            ondelete='CASCADE'
        ),
    )
    
    # 关系
    order = relationship('Order', back_populates='order_items')
    store_book = relationship('StoreBook', back_populates='order_items')

class BookImage(Base):
    __tablename__ = 'book_images'
    
    book_id = Column(String(255), ForeignKey('book.id', ondelete='CASCADE'), primary_key=True)
    image_id = Column(String(255), primary_key=True)
    image_path = Column(Text, nullable=False)
    
    # 关系
    base_book = relationship('BaseBook', back_populates='book_images')

def init_database():
    """初始化数据库，创建所有表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise
