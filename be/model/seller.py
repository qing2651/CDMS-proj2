import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime
from .store import User, Store, BaseBook, StoreBook, Order
from .db_config import SessionLocal
from .user import UserManager
from .error import (
    error_non_exist_user_id,
    error_exist_store_id,
    error_non_exist_store_id,
    error_non_exist_book_id,
    error_authorization_fail,
    error_bad_request,
    error_internal,
    error_invalid_order_id,
    error_exist_book_id
)
from sqlalchemy import text

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SellerManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SellerManager, cls).__new__(cls)
            cls._instance.user_manager = UserManager()
        return cls._instance
    
    def __init__(self):
        pass
    
    def verify_token(self, user_id: str, token: str) -> bool:
        """验证token是否有效"""
        valid, token_user_id = self.user_manager._verify_token(token, user_id)
        return valid and token_user_id == user_id
    
    def create_store(self, user_id: str, store_id: str) -> int:
        """
        创建商店
        返回值: 状态码（200表示成功）
        """
        try:
            with SessionLocal() as db:
                # 开始事务
                db.begin()
                
                # 查找用户
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    logger.warning(f"用户不存在: {user_id}")
                    return error_non_exist_user_id(user_id)[0]
                
                # 检查商店ID是否已存在
                existing_store = db.query(Store).filter(Store.store_id == store_id).first()
                if existing_store:
                    logger.warning(f"商店已存在: {store_id}")
                    return error_exist_store_id(store_id)[0]
                
                # 创建商店
                new_store = Store(
                    store_id=store_id,
                    owner_id=user_id
                )
                db.add(new_store)
                db.commit()
                logger.info(f"商店创建成功: {store_id}")
                return 200
                
        except Exception as e:
            logger.error(f"创建商店失败: {str(e)}")
            return error_internal(str(e))[0]
    
    def add_book(self, user_id: str, store_id: str, book_info: dict, stock_level: int) -> int:
        """
        添加图书
        返回值: 状态码（200表示成功）
        """
        try:
            with SessionLocal() as db:
                # 开始事务
                db.begin()
                
                # 1. 验证用户是否存在
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    logger.warning(f"用户不存在: {user_id}")
                    return error_non_exist_user_id(user_id)[0]
                
                # 2. 验证商店是否存在，并锁定商店记录
                store = db.query(Store).filter(Store.store_id == store_id).with_for_update().first()
                if not store:
                    logger.warning(f"商店不存在: {store_id}")
                    return error_non_exist_store_id(store_id)[0]
                
                # 3. 验证用户是否是商店所有者
                if store.owner_id != user_id:
                    logger.warning(f"用户不是商店所有者: user_id={user_id}, store_id={store_id}")
                    return error_authorization_fail("不是商店所有者")[0]
                
                # 4. 验证图书信息是否完整
                book_id = book_info.get('id')
                if not book_id:
                    logger.warning("缺少图书ID")
                    return error_bad_request("缺少图书ID")[0]
                
                # 5. 验证库存是否合法
                if stock_level < 0:
                    logger.warning(f"库存不能为负数: {stock_level}")
                    return error_bad_request("库存不能为负数")[0]
                
                try:
                    # 6. 检查图书是否已在商店中
                    existing_store_book = db.query(StoreBook).filter(
                        StoreBook.store_id == store_id,
                        StoreBook.book_id == book_id
                    ).with_for_update().first()
                    
                    if existing_store_book:
                        logger.warning(f"图书已存在于商店中: store_id={store_id}, book_id={book_id}")
                        return error_exist_book_id(book_id)[0]
                    
                    # 7. 检查并添加基本图书信息到book表
                    base_book = db.query(BaseBook).filter(BaseBook.id == book_id).with_for_update().first()
                    
                    if not base_book:
                        # 添加到book表
                        base_book = BaseBook(
                            id=book_id,
                            title=book_info.get("title", ""),
                            author=book_info.get("author", ""),
                            publisher=book_info.get("publisher", ""),
                            original_title=book_info.get("original_title", ""),
                            translator=book_info.get("translator", ""),
                            pub_year=book_info.get("pub_year", ""),
                            pages=book_info.get("pages", 0),
                            price=float(book_info.get("price", 0)),
                            currency_unit=book_info.get("currency_unit", "CNY"),
                            binding=book_info.get("binding", ""),
                            isbn=book_info.get("isbn", ""),
                            author_intro=book_info.get("author_intro", ""),
                            book_intro=book_info.get("book_intro", ""),
                            content=book_info.get("content", ""),
                            tags=",".join(book_info.get("tags", []))
                        )
                        db.add(base_book)
                    
                    # 8. 添加商店图书关联信息到store_books表
                    store_book = StoreBook(
                        store_id=store_id,
                        book_id=book_id,
                        stock_level=stock_level,
                        price=float(book_info.get("price", 0))
                    )
                    db.add(store_book)
                    
                    db.commit()
                    logger.info(f"图书添加成功: store_id={store_id}, book_id={book_id}")
                    return 200
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"添加图书失败: {str(e)}")
                    return error_internal(str(e))[0]
                
        except Exception as e:
            logger.error(f"添加图书失败: {str(e)}")
            return error_internal(str(e))[0]
    
    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int) -> int:
        """
        增加库存
        返回值: 状态码（200表示成功）
        """
        try:
            with SessionLocal() as db:
                # 开始事务
                db.begin()
                
                # 1. 验证用户是否存在
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    logger.warning(f"用户不存在: {user_id}")
                    return error_non_exist_user_id(user_id)[0]
                
                # 2. 验证商店是否存在，并锁定商店记录
                store = db.query(Store).filter(Store.store_id == store_id).with_for_update().first()
                if not store:
                    logger.warning(f"商店不存在: {store_id}")
                    return error_non_exist_store_id(store_id)[0]
                
                # 3. 验证用户是否是商店所有者
                if store.owner_id != user_id:
                    logger.warning(f"用户不是商店所有者: user_id={user_id}, store_id={store_id}")
                    return error_authorization_fail("不是商店所有者")[0]
                
                # 4. 验证库存增加值是否合法
                if add_stock_level < 0:
                    logger.warning(f"库存增加值不能为负数: {add_stock_level}")
                    return error_bad_request("库存增加值不能为负数")[0]
                
                # 5. 查找图书并锁定记录
                store_book = db.query(StoreBook).filter(
                    StoreBook.store_id == store_id,
                    StoreBook.book_id == book_id
                ).with_for_update().first()
                
                if not store_book:
                    logger.warning(f"图书不存在: book_id={book_id}")
                    return error_non_exist_book_id(book_id)[0]
                
                # 6. 更新库存
                try:
                    store_book.stock += add_stock_level
                    db.commit()
                    logger.info(f"库存更新成功: book_id={book_id}, new_stock_level={store_book.stock}")
                    return 200
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"库存更新失败: {str(e)}")
                    return error_internal(str(e))[0]
                    
        except Exception as e:
            logger.error(f"增加库存失败: {str(e)}")
            return error_internal(str(e))[0]
    
    def deliver_order(self, user_id: str, order_id: str) -> int:
        """
        发货
        返回值: 状态码（200表示成功）
        """
        try:
            with SessionLocal() as db:
                # 开始事务
                db.begin()
                
                # 验证用户
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    logger.warning(f"用户不存在: {user_id}")
                    return error_non_exist_user_id(user_id)[0]
                
                # 查找订单并锁定记录
                order = db.query(Order).filter(Order.order_id == order_id).with_for_update().first()
                if not order:
                    logger.warning(f"订单不存在: {order_id}")
                    return error_invalid_order_id(order_id)[0]
                
                # 验证商店所有者并锁定商店记录
                store = db.query(Store).filter(Store.store_id == order.store_id).with_for_update().first()
                if store.owner_id != user_id:
                    logger.warning(f"用户不是商店所有者: user_id={user_id}, store_id={order.store_id}")
                    return error_authorization_fail("不是商店所有者")[0]
                
                # 验证订单状态
                if order.status != "paid":
                    logger.warning(f"订单状态错误: {order_id}, status={order.status}")
                    return error_invalid_order_id(order_id)[0]
                
                try:
                    # 更新订单状态
                    order.status = "delivering"
                    order.delivery_time = datetime.now()
                    
                    db.commit()
                    logger.info(f"订单发货成功: {order_id}")
                    return 200
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"更新订单状态失败: {str(e)}")
                    return error_internal(str(e))[0]
                
        except Exception as e:
            logger.error(f"发货失败: {str(e)}")
            return error_internal(str(e))[0]
