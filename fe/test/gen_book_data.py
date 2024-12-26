import random
import uuid
from fe import conf
from fe.access.new_seller import register_new_seller
from fe.access.book import BookDB


class GenBook:
    _book_db = None  # 静态变量用于缓存
    _cached_books = None
    
    @classmethod
    def _init_book_db(cls):
        if cls._book_db is None:
            cls._book_db = BookDB(conf.Use_Large_DB)
            # 预加载一定数量的图书
            cls._cached_books = cls._book_db.get_book_info(0, 100)
    
    def __init__(self, user_id, store_id):
        self.user_id = user_id
        self.store_id = store_id
        self.password = self.user_id
        self.seller = register_new_seller(self.user_id, self.password)
        code = self.seller.create_store(store_id)
        assert code == 200
        self.__init_book_list__()
        self._init_book_db()

    def __init_book_list__(self):
        self.buy_book_info_list = []
        self.buy_book_id_list = []

    def gen(
        self, non_exist_book_id: bool, low_stock_level, max_book_count: int = 10
    ) -> (bool, []):
        self.__init_book_list__()
        ok = True
        
        # 从缓存中随机选择图书
        size = random.randint(1, min(max_book_count, len(self._cached_books)))
        books = random.sample(self._cached_books, size)
        
        book_id_exist = []
        book_id_stock_level = {}
        
        for bk in books:
            if low_stock_level:
                stock_level = random.randint(0, 10)  # 减少库存范围
            else:
                stock_level = random.randint(2, 20)  # 减少库存范围
            
            code = self.seller.add_book(self.store_id, stock_level, bk)
            assert code == 200
            book_id_stock_level[bk.id] = stock_level
            book_id_exist.append(bk)

        for bk in book_id_exist:
            stock_level = book_id_stock_level[bk.id]
            if stock_level > 1:
                buy_num = random.randint(1, min(stock_level, 5))  # 限制购买数量
            else:
                buy_num = 0
                
            if non_exist_book_id:
                bk.id = bk.id + "_x"
            if low_stock_level:
                buy_num = stock_level + 1
                
            self.buy_book_info_list.append((bk, buy_num))

        for item in self.buy_book_info_list:
            book_id = item[0].id
            self.buy_book_id_list.append((book_id, item[1]))
            
        return ok, self.buy_book_id_list
