import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
import logging
from contextlib import contextmanager

# 配置日志
logger = logging.getLogger(__name__)

# 使用远程MySQL数据库
DATABASE_URL = "mysql+pymysql://bookstore:HGHEnZbbzDM7nats@103.56.115.84:3306/bookstore"

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine)

# 声明基类
Base = declarative_base()

def get_db():
    """获取数据库连接"""
    try:
        # 创建一个新的数据库连接
        connection = engine.raw_connection()
        return connection
    except Exception as e:
        logger.error(f"获取数据库连接失败: {str(e)}")
        raise

def init_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    try:
        # 直接使用engine创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化成功")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise

def clean_db():
    """清理并重新创建数据库表"""
    try:
        logger.info("开始清理数据库...")
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        logger.info("所有表已删除")
        
        # 重新创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("所有表已重新创建")
        
        return True
    except Exception as e:
        logger.error(f"数据库清理失败: {str(e)}")
        raise

