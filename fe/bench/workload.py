import logging
import uuid
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from fe.access import book
from fe.access.new_seller import register_new_seller
from fe.access.new_buyer import register_new_buyer
from fe.access.buyer import Buyer
from fe import conf
from sqlalchemy import create_engine, text

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewOrder:
    def __init__(self, buyer: Buyer, store_id: str, book_id_and_count: List[Tuple[str, int]]):
        self.buyer = buyer
        self.store_id = store_id
        self.book_id_and_count = book_id_and_count

    def run(self) -> Tuple[bool, str]:
        try:
            code, order_id = self.buyer.new_order(self.store_id, self.book_id_and_count)
            return code == 200, order_id
        except Exception as e:
            logger.error(f"创建订单失败: {str(e)}")
            return False, ""

class Payment:
    def __init__(self, buyer: Buyer, order_id: str):
        self.buyer = buyer
        self.order_id = order_id

    def run(self) -> bool:
        try:
            code = self.buyer.payment(self.order_id)
            return code == 200
        except Exception as e:
            logger.error(f"支付订单失败: {str(e)}")
            return False

class Workload:
    def __init__(self):
        self.uuid = str(uuid.uuid1())
        self.book_ids: Dict[str, List[str]] = {}
        self.buyer_ids: List[str] = []
        self.store_ids: List[str] = []
        self.seller_ids: List[str] = []
        self.session = {}
        self.start_time = time.time()
        
        # 初始化统计数据
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        
        # 线程安全
        self.lock = threading.Lock()
        
        logger.info("初始化工作负载...")
        
        # 初始化数据库连接
        try:
            self.engine = create_engine(
                f'mysql+pymysql://{conf.DB_User}:{conf.DB_Password}@{conf.DB_Host}:{conf.DB_Port}/{conf.DB_Name}'
            )
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise

    def to_seller_id_and_password(self, no: int) -> Tuple[str, str]:
        """生成卖家ID和密码"""
        seller_id = f"seller_{no}_{self.uuid}"
        password = seller_id
        return seller_id, password

    def to_buyer_id_and_password(self, no: int) -> Tuple[str, str]:
        """生成买家ID和密码"""
        buyer_id = f"buyer_{no}_{self.uuid}"
        password = buyer_id
        return buyer_id, password

    def to_store_id(self, seller_no: int, store_no: int) -> str:
        """生成商店ID"""
        return f"store_{seller_no}_{store_no}_{self.uuid}"

    def gen_database(self):
        """生成测试数据"""
        try:
            logger.info("开始加载数据...")
            
            # 创建卖家和商店
            with ThreadPoolExecutor() as executor:
                seller_futures = []
                for seller_no in range(conf.Seller_N):
                    future = executor.submit(self._create_seller_and_stores, seller_no)
                    seller_futures.append(future)
                
                # 等待所有卖家创建完成
                for future in as_completed(seller_futures):
                    if not future.result():
                        logger.error("创建卖家和商店失败")
                        return False
            
            # 创建买家
            with ThreadPoolExecutor() as executor:
                buyer_futures = []
                for buyer_no in range(conf.Buyer_N):
                    future = executor.submit(self._create_buyer, buyer_no)
                    buyer_futures.append(future)
                
                # 等待所有买家创建完成
                for future in as_completed(buyer_futures):
                    if not future.result():
                        logger.error("创建买家失败")
                        return False
            
            logger.info(f"数据加载完成，耗时: {time.time() - self.start_time:.2f}秒")
            return True
            
        except Exception as e:
            logger.error(f"生成测试数据失败: {str(e)}")
            return False

    def _create_seller_and_stores(self, seller_no: int):
        """创建卖家和商店"""
        try:
            # 生成卖家ID和密码
            seller_id, password = self.to_seller_id_and_password(seller_no)
            
            # 注册新卖家
            code = register_new_seller(seller_id, password)
            if code != 200:
                logger.error(f"创建卖家失败，状态码：{code}")
                return False
            
            # 创建卖家会话
            from fe.access.seller import Seller
            seller = Seller(conf.URL, seller_id, password)
            code = seller.login()
            if code != 200:
                logger.error(f"卖家登录失败，状态码：{code}")
                return False
            
            # 存储卖家信息
            self.session[seller_id] = seller
            self.seller_ids.append(seller_id)
            
            # 为卖家创建商店
            for store_no in range(conf.Store_N):
                store_id = self.to_store_id(seller_no, store_no)
                code = seller.create_store(store_id)
                if code != 200:
                    logger.error(f"创建商店失败，状态码：{code}")
                    return False
                
                self.store_ids.append(store_id)
                self.book_ids[store_id] = []
                
                # 为商店添加图书
                for book_no in range(conf.Book_N):
                    book_id = f"book_{seller_no}_{store_no}_{book_no}_{self.uuid}"
                    code = seller.add_book(store_id, book_id, conf.Default_Book_Price, conf.Default_Stock_Level)
                    if code != 200:
                        logger.error(f"添加图书失败，状态码：{code}")
                        return False
                    
                    self.book_ids[store_id].append(book_id)
            
            return True
            
        except Exception as e:
            logger.error(f"创建卖家和商店时发生错误: {str(e)}")
            return False

    def _add_books_to_store(self, seller, store_id: str):
        """添加图书到商店"""
        try:
            # 获取图书信息
            cursor = self.engine.connect()
            query = text("""
                SELECT book_id, title, author, publisher, book_intro, stock_level, price
                FROM book LIMIT :limit
            """)
            result = cursor.execute(query, {"limit": conf.Book_N})
            books = result.fetchall()
            cursor.close()
            
            # 添加图书到商店
            for book in books:
                book_info = {
                    "book_id": book[0],
                    "title": book[1],
                    "author": book[2],
                    "publisher": book[3],
                    "book_intro": book[4],
                    "stock_level": conf.Default_Stock_Level,
                    "price": float(book[6])
                }
                
                code = seller.add_book(store_id, book_info)
                if not isinstance(code, int) or code != 200:
                    logger.error(f"添加图书失败，状态码：{code}")
                    return False
                    
                self.book_ids[store_id].append(book_info["book_id"])
                    
            return True
            
        except Exception as e:
            logger.error(f"添加图书到商店时发生错误: {str(e)}")
            return False

    def _create_buyer(self, buyer_no: int):
        """创建买家"""
        try:
            # 生成买家ID和密码
            buyer_id, password = self.to_buyer_id_and_password(buyer_no)
            
            # 注册新买家
            code = register_new_buyer(buyer_id, password)
            if code != 200:
                logger.error(f"创建买家失败，状态码：{code}")
                return False
            
            # 创建买家会话
            buyer = Buyer(conf.URL, buyer_id, password)
            code = buyer.login()
            if code != 200:
                logger.error(f"买家登录失败，状态码：{code}")
                return False
                
            self.session[buyer_id] = buyer
            
            # 设置初始余额
            code = buyer.add_funds(conf.Default_User_Funds)
            if code != 200:
                logger.error(f"设置买家余额失败，状态码：{code}")
                return False
            
            self.buyer_ids.append(buyer_id)
            return True
            
        except Exception as e:
            logger.error(f"创建买家时发生错误: {str(e)}")
            return False

    def get_new_order(self) -> NewOrder:
        """生成新订单"""
        try:
            # 确保有可用的买家和商店
            if not self.buyer_ids or not self.store_ids:
                logger.error("没有可用的买家或商店")
                raise ValueError("No available buyers or stores")

            # 随机选择买家和商店
            buyer_id = random.choice(self.buyer_ids)
            store_id = random.choice(self.store_ids)
            
            # 确保商店有可用的图书
            if store_id not in self.book_ids or not self.book_ids[store_id]:
                logger.error(f"商店 {store_id} 没有可用的图书")
                raise ValueError(f"No books available in store {store_id}")
            
            # 随机选择1-5本书
            n_books = random.randint(1, min(5, len(self.book_ids[store_id])))
            books = random.sample(self.book_ids[store_id], n_books)
            
            # 生成购买数量（1-3本）
            book_id_and_count = [(book_id, random.randint(1, 3)) for book_id in books]
            
            # 获取买家会话
            buyer = self.session.get(buyer_id)
            if not buyer:
                logger.error(f"买家 {buyer_id} 未找到")
                raise ValueError(f"Buyer {buyer_id} not found")
                
            return NewOrder(buyer, store_id, book_id_and_count)
            
        except Exception as e:
            logger.error(f"生成新订单失败: {str(e)}")
            raise

    def update_stat(self, n_new_order: int, n_payment: int, n_new_order_ok: int,
                   n_payment_ok: int, time_new_order: float, time_payment: float):
        """更新统计信息"""
        self.total_requests += n_new_order + n_payment
        self.successful_requests += n_new_order_ok + n_payment_ok
        self.failed_requests += (n_new_order - n_new_order_ok) + (n_payment - n_payment_ok)
        self.total_response_time += time_new_order + time_payment

    def _init_test_user(self):
        """初始化测试用户"""
        try:
            # 使用正确的方式注册测试用户
            from fe.access.new_buyer import register_new_buyer
            test_user = register_new_buyer("test_user", "test_password")
            return True
        except Exception as e:
            logger.error(f"初始化测试用户失败: {str(e)}")
            return False
