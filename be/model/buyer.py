import logging
import uuid
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from typing import List, Dict, Optional, Tuple
from .store import User, Store, BaseBook, StoreBook, Order, OrderItem
from .db_config import SessionLocal
from .user import UserManager
from .error import (
    error_non_exist_user_id,
    error_non_exist_store_id,
    error_non_exist_book_id,
    error_stock_level_low,
    error_not_sufficient_funds,
    error_invalid_order_id,
    error_authorization_fail,
    error_internal
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuyerManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BuyerManager, cls).__new__(cls)
            cls._instance.user_manager = UserManager()
        return cls._instance
    
    def __init__(self):
        pass
    
    def search_books(self, keyword: str, page: int = 1, per_page: int = 10, sort_by: str = None, store_id: str = None, search_type: str = "normal") -> Dict:
        """
        搜索图书
        :param keyword: 搜索关键词
        :param page: 页码（从1开始）
        :param per_page: 每页数量
        :param sort_by: 排序字段（price_asc, price_desc, title_asc, title_desc）
        :param store_id: 商店ID（None表示全站搜索）
        :param search_type: 搜索类型（normal: 普通搜索, fulltext: 全文搜索）
        :return: 包含分页信息和图书列表的字典
        """
        try:
            with SessionLocal() as db:
                # 构建基础查询
                query = db.query(BaseBook, StoreBook).join(
                    StoreBook, BaseBook.id == StoreBook.book_id, isouter=True
                )
                
                # 添加搜索条件
                if keyword:
                    if search_type == "fulltext":
                        # 使用全文搜索
                        query = query.filter(text(
                            "MATCH(book.title, book.tags, book.content) AGAINST(:keyword IN BOOLEAN MODE)"
                        ).params(keyword=keyword))
                    else:
                        # 使用普通搜索
                        query = query.filter(
                            or_(
                                BaseBook.title.ilike(f"%{keyword}%"),
                                BaseBook.author.ilike(f"%{keyword}%"),
                                BaseBook.publisher.ilike(f"%{keyword}%"),
                                BaseBook.tags.ilike(f"%{keyword}%"),
                                BaseBook.content.ilike(f"%{keyword}%")
                            )
                        )
                
                # 添加商店过滤
                if store_id:
                    query = query.filter(StoreBook.store_id == store_id)
                
                # 添加排序
                if sort_by:
                    if sort_by == "price_asc":
                        query = query.order_by(StoreBook.price.asc())
                    elif sort_by == "price_desc":
                        query = query.order_by(StoreBook.price.desc())
                    elif sort_by == "title_asc":
                        query = query.order_by(BaseBook.title.asc())
                    elif sort_by == "title_desc":
                        query = query.order_by(BaseBook.title.desc())
                
                # 计算总数（使用子查询优化性能）
                total = query.count()
                
                # 添加分页（使用 limit/offset 优化性能）
                offset = (page - 1) * per_page
                query = query.offset(offset).limit(per_page)
                
                # 执行查询并缓存结果
                results = query.all()
                
                # 格式化结果
                books = []
                for base_book, store_book in results:
                    book_data = {
                        "id": base_book.id,
                        "store_id": store_book.store_id if store_book else None,
                        "title": base_book.title,
                        "author": base_book.author,
                        "publisher": base_book.publisher,
                        "price": float(store_book.price) if store_book else float(base_book.price),
                        "stock": store_book.stock if store_book else 0,
                        "tags": base_book.tags.split(",") if base_book.tags else [],
                        "content": base_book.content,
                        "book_intro": base_book.book_intro
                    }
                    books.append(book_data)
                
                return {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page,
                    "books": books
                }
                
        except Exception as e:
            logger.error(f"搜索图书失败: {str(e)}")
            return {
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "books": []
            }
    
    def add_funds(self, user_id: str, password: str, amount: float) -> int:
        """
        用户充值/提现
        返回值: 状态码（200表示成功）
        """
        try:
            with SessionLocal() as db:
                # 开始事务
                db.begin()
                
                # 验证用户
                user = db.query(User).filter(User.user_id == user_id).with_for_update().first()
                if not user:
                    logger.warning(f"用户不存在: {user_id}")
                    return error_non_exist_user_id(user_id)[0]
                
                # 验证密码
                if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                    logger.warning(f"密码错误: {user_id}")
                    return error_authorization_fail("密码错误")[0]
                
                # 将金额转换为 Decimal 类型
                from decimal import Decimal
                amount = Decimal(str(amount))
                
                # 验证余额（如果是提现）
                if amount < 0 and user.balance < abs(amount):
                    logger.warning(f"余额不足: user={user_id}, balance={user.balance}, amount={amount}")
                    return error_not_sufficient_funds("余额不足")[0]
                
                # 更新余额
                try:
                    user.balance += amount
                    db.commit()
                    logger.info(f"用户 {user_id} {'充值' if amount > 0 else '提现'}成功: {abs(amount)}")
                    return 200
                except Exception as e:
                    db.rollback()
                    logger.error(f"更新余额失败: {str(e)}")
                    return error_internal(str(e))[0]
                
        except Exception as e:
            logger.error(f"{'充值' if amount > 0 else '提现'}失败: {str(e)}")
            return error_internal(str(e))[0]
    
    def new_order(self, user_id: str, store_id: str, books: List[Dict]) -> Tuple[int, Optional[str]]:
        """
        创建订单
        返回值: (状态码, 订单ID)
        """
        try:
            with SessionLocal() as db:
                # 开始事务
                db.begin()
                
                # 验证用户
                user = db.query(User).filter(User.user_id == user_id).with_for_update().first()
                if not user:
                    logger.warning(f"用户不存在: {user_id}")
                    return error_non_exist_user_id(user_id)[0], None
                
                # 验证商店
                store = db.query(Store).filter(Store.store_id == store_id).with_for_update().first()
                if not store:
                    logger.warning(f"商店不存在: {store_id}")
                    return error_non_exist_store_id(store_id)[0], None
                
                # 验证图书库存并计算总价
                total_price = 0
                order_books = []
                for book_info in books:
                    # 查找图书和库存信息
                    store_book = db.query(StoreBook).join(BaseBook).filter(
                        StoreBook.store_id == store_id,
                        StoreBook.book_id == book_info['id']
                    ).with_for_update().first()
                    
                    if not store_book:
                        logger.warning(f"图书不存在: book_id={book_info['id']}")
                        return error_non_exist_book_id(book_info['id'])[0], None
                    
                    # 检查库存
                    if store_book.stock_level < book_info["count"]:
                        logger.warning(f"库存不足: book_id={book_info['id']}, stock={store_book.stock_level}, requested={book_info['count']}")
                        return error_stock_level_low(book_info['id'])[0], None
                    
                    order_books.append((store_book, book_info["count"]))
                    total_price += store_book.price * book_info["count"]

                try:
                    # 创建订单
                    order_id = str(uuid.uuid4())
                    # 设置过期时间为30分钟后
                    expire_time = datetime.now() + timedelta(minutes=30)
                    new_order = Order(
                        order_id=order_id,
                        user_id=user_id,
                        store_id=store_id,
                        total_price=total_price,
                        status="pending",
                        create_time=datetime.now(),
                        expire_time=expire_time
                    )
                    db.add(new_order)
                    
                    # 创建订单项并减少库存
                    for store_book, count in order_books:
                        order_item = OrderItem(
                            order_id=order_id,
                            book_id=store_book.book_id,
                            store_id=store_id,
                            count=count,
                            price=store_book.price
                        )
                        db.add(order_item)
                        store_book.stock_level -= count
                    
                    db.commit()
                    logger.info(f"订单创建成功: {order_id}")
                    return 200, order_id
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"创建订单失败: {str(e)}")
                    return error_internal(str(e))[0], None

        except Exception as e:
            logger.error(f"创建订单失败: {str(e)}")
            return error_internal(str(e))[0], None
    
    def check_order_expired(self, order_id: str) -> bool:
        """
        检查订单是否过期
        :param order_id: 订单ID
        :return: 是否过期
        """
        try:
            with SessionLocal() as db:
                order = db.query(Order).filter(Order.order_id == order_id).first()
                if not order:
                    return False
                
                # 只检查待支付状态的订单
                if order.status != "pending":
                    return False
                
                # 检查是否过期
                if order.expire_time and datetime.now() > order.expire_time:
                    # 更新订单状态为已取消
                    order.status = "cancelled"
                    db.commit()
                    logger.info(f"订单已过期自动取消: {order_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"检查订单过期失败: {str(e)}")
            return False
    
    def payment(self, user_id: str, password: str, order_id: str) -> int:
        """
        支付订单
        返回值: 状态码（200表示成功）
        """
        try:
            with SessionLocal() as db:
                # 先检查订单是否过期
                if self.check_order_expired(order_id):
                    logger.warning(f"订单已过期: {order_id}")
                    return error_invalid_order_id(order_id)[0]  # 518
                
                # 验证用户
                user = db.query(User).filter(User.username == user_id).first()
                if not user:
                    logger.warning(f"用户不存在: {user_id}")
                    return error_non_exist_user_id(user_id)[0]  # 511
                
                # 验证密码
                if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                    logger.warning(f"密码错误: {user_id}")
                    return error_authorization_fail("密码错误")[0]  # 401
                
                # 查找订单
                order = db.query(Order).filter(
                    Order.order_id == order_id,
                    Order.user_id == user.user_id
                ).first()
                
                if not order:
                    logger.warning(f"订单不存在: {order_id}")
                    return error_invalid_order_id(order_id)[0]  # 518
                
                if order.status != "pending":
                    logger.warning(f"订单状态错误: {order_id}, status={order.status}")
                    return error_invalid_order_id(order_id)[0]  # 518
                
                # 检查余额
                if user.balance < order.total_price:
                    logger.warning(f"余额不足: user={user_id}, balance={user.balance}, required={order.total_price}")
                    return error_not_sufficient_funds(order_id)[0]  # 519
                
                try:
                    # 扣除余额并更新订单状态
                    user.balance -= order.total_price
                    order.status = "paid"
                    order.payment_time = datetime.now()
                    
                    db.commit()
                    logger.info(f"订单支付成功: {order_id}")
                    return 200
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"更新订单状态失败: {str(e)}")
                    return error_internal("更新订单状态失败")[0]  # 530
                
        except Exception as e:
            logger.error(f"支付订单失败: {str(e)}")
            return error_internal(str(e))[0]  # 530
    
    def receive_order(self, user_id: str, order_id: str) -> int:
        """
        确认收货
        返回值: 状态码（200表示成功）
        """
        try:
            with SessionLocal() as db:
                # 验证用户
                user = db.query(User).filter(User.username == user_id).first()
                if not user:
                    logger.warning(f"用户不存在: {user_id}")
                    return error_non_exist_user_id(user_id)[0]  # 511
                
                # 查找订单
                order = db.query(Order).filter(
                    Order.order_id == order_id,
                    Order.user_id == user.user_id
                ).first()
                
                if not order:
                    logger.warning(f"订单不存在: {order_id}")
                    return error_invalid_order_id(order_id)[0]  # 518
                
                # 验证订单状态
                if order.status != "delivering":
                    logger.warning(f"订单状态错误: {order_id}, status={order.status}")
                    return error_invalid_order_id(order_id)[0]  # 518
                
                try:
                    # 更新订单状态
                    order.status = "received"
                    order.receive_time = datetime.now()
                    
                    db.commit()
                    logger.info(f"订单收货成功: {order_id}")
                    return 200
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"更新订单状态失败: {str(e)}")
                    return error_internal("更新订单状态失败")[0]  # 530
                
        except Exception as e:
            logger.error(f"确认收货失败: {str(e)}")
            return error_internal(str(e))[0]  # 530
    
    def check_expired_orders(self) -> int:
        """
        批量检查并取消过期订单
        :return: 取消的订单数量
        """
        try:
            with SessionLocal() as db:
                # 查找所有过期的待支付订单
                expired_orders = db.query(Order).filter(
                    Order.status == "pending",
                    Order.expire_time < datetime.now()
                ).all()
                
                cancelled_count = 0
                for order in expired_orders:
                    try:
                        # 更新订单状态为已取消
                        order.status = "cancelled"
                        cancelled_count += 1
                    except Exception as e:
                        logger.error(f"取消订单失败: {str(e)}")
                        continue
                
                try:
                    db.commit()
                    logger.info(f"成功取消 {cancelled_count} 个过期订单")
                except Exception as e:
                    db.rollback()
                    logger.error(f"提交取消订单更改失败: {str(e)}")
                    return 0
                
                return cancelled_count
                
        except Exception as e:
            logger.error(f"批量检查过期订单失败: {str(e)}")
            return 0
    
    def cancel_order(self, user_id: str, order_id: str) -> int:
        """
        取消订单
        返回值: 状态码（200表示成功）
        """
        try:
            with SessionLocal() as db:
                # 验证用户
                user = db.query(User).filter(User.username == user_id).first()
                if not user:
                    logger.warning(f"用户不存在: {user_id}")
                    return error_non_exist_user_id(user_id)[0]  # 511
                
                # 查找订单
                order = db.query(Order).filter(Order.order_id == order_id).first()
                if not order:
                    logger.warning(f"订单不存在: {order_id}")
                    return error_invalid_order_id(order_id)[0]  # 518
                
                # 验证订单所有者
                if order.user_id != user.user_id:
                    logger.warning(f"用户不是订单所有者: user_id={user_id}, order_id={order_id}")
                    return error_authorization_fail("不是订单所有者")[0]  # 401
                
                # 验证订单状态
                if order.status != "pending":
                    logger.warning(f"订单状态错误: {order_id}, status={order.status}")
                    return error_invalid_order_id(order_id)[0]  # 518
                
                try:
                    # 更新订单状态
                    order.status = "cancelled"
                    
                    # 恢复库存
                    for item in order.order_items:
                        book = db.query(BaseBook).filter(BaseBook.book_id == item.book_id).first()
                        if book:
                            book.stock_level += item.count
                    
                    db.commit()
                    logger.info(f"订单取消成功: {order_id}")
                    return 200
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"取消订单失败: {str(e)}")
                    return error_internal("取消订单失败")[0]  # 530
                
        except Exception as e:
            logger.error(f"取消订单失败: {str(e)}")
            return error_internal(str(e))[0]  # 530
