import sqlite3
import json
from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine
import os
from pathlib import Path
from sqlalchemy import inspect
import logging
from .store import Base, User, Store, BaseBook, StoreBook, Order, OrderItem, BookImage

# 配置日志
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = "mysql+pymysql://bookstore:HGHEnZbbzDM7nats@103.56.115.84:3306/bookstore"
engine = create_engine(DATABASE_URL)

def migrate_sqlite_to_mysql():
    """从SQLite导入数据到MySQL，只在book表不存在时导入"""
    logger.info("开始检查book表是否存在...")
    # 检查book表是否存在
    with engine.connect() as connection:
        inspector = inspect(engine)
        if 'book' in inspector.get_table_names():
            logger.info("book表已存在，跳过数据导入")
            return True
    
    logger.info("book表不存在，开始创建表...")
    
    # 按顺序创建表
    tables = [
        User.__table__,
        Store.__table__,
        BaseBook.__table__,
        StoreBook.__table__,
        Order.__table__,
        OrderItem.__table__,
        BookImage.__table__
    ]
    
    # 创建表
    for table in tables:
        try:
            logger.info(f"创建表 {table.name}...")
            table.create(bind=engine, checkfirst=True)
        except Exception as e:
            logger.error(f"创建表 {table.name} 失败: {str(e)}")
            raise
    
    logger.info("表创建成功，开始导入数据...")
    
    # 获取SQLite数据库路径
    current_dir = Path(__file__).parent
    fe_path = current_dir.parent.parent / "fe"
    sqlite_db_path = fe_path / "data" / "book.db"
    
    if not sqlite_db_path.exists():
        logger.error(f"SQLite数据库文件不存在: {sqlite_db_path}")
        return False
    
    try:
        logger.info("连接SQLite数据库...")
        # 连接SQLite数据库
        sqlite_conn = sqlite3.connect(str(sqlite_db_path))
        sqlite_cursor = sqlite_conn.cursor()
        
        logger.info("获取图书数据...")
        # 获取所有图书数据
        sqlite_cursor.execute("SELECT * FROM book")
        books = sqlite_cursor.fetchall()
        
        # 获取列名
        columns = [description[0] for description in sqlite_cursor.description]
        
        logger.info(f"开始导入 {len(books)} 本图书...")
        # 使用SQLAlchemy连接MySQL
        with engine.connect() as mysql_conn:
            # 为每本书创建插入语句
            for i, book_data in enumerate(books, 1):
                try:
                    # 构建数据字典
                    book_dict = dict(zip(columns, book_data))
                    
                    # 构建INSERT语句
                    insert_stmt = text("""
                        INSERT INTO book (
                            id, title, author, publisher, original_title, 
                            translator, pub_year, pages, price, currency_unit,
                            binding, isbn, author_intro, book_intro, content, 
                            tags, picture
                        ) VALUES (
                            :id, :title, :author, :publisher, :original_title,
                            :translator, :pub_year, :pages, :price, :currency_unit,
                            :binding, :isbn, :author_intro, :book_intro, :content,
                            :tags, :picture
                        )
                    """)
                    
                    # 执行插入
                    mysql_conn.execute(insert_stmt, book_dict)
                    if i % 100 == 0:  # 每导入100本书记录一次日志
                        logger.info(f"已导入 {i} 本图书...")
                        mysql_conn.commit()  # 每100条记录提交一次事务
                except Exception as e:
                    logger.error(f"导入第 {i} 本图书时失败: {str(e)}")
                    continue
            
            # 提交最后的事务
            mysql_conn.commit()
        
        logger.info(f"成功从SQLite导入了 {len(books)} 本图书")
        return True
        
    except Exception as e:
        logger.error(f"数据迁移失败: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        print("开始迁移SQLite数据到MySQL...")
        if migrate_sqlite_to_mysql():
            print("数据迁移成功！")
        else:
            print("数据迁移失败！")
    except Exception as e:
        print(f"迁移脚本执行失败: {str(e)}")
