import pytest
from fe import conf
from fe.access.new_seller import register_new_seller
from fe.access import book
import uuid


class TestAddStockLevel:
    @classmethod
    def setup_class(cls):
        # 类级别的设置，只执行一次
        cls.user_id = "test_add_book_stock_level1_user_{}".format(str(uuid.uuid1()))
        cls.store_id = "test_add_book_stock_level1_store_{}".format(str(uuid.uuid1()))
        cls.password = cls.user_id
        cls.seller = register_new_seller(cls.user_id, cls.password)
        
        code = cls.seller.create_store(cls.store_id)
        assert code == 200
        
        # 只获取一本书进行测试
        book_db = book.BookDB(conf.Use_Large_DB)
        cls.books = book_db.get_book_info(0, 1)
        for bk in cls.books:
            code = cls.seller.add_book(cls.store_id, 0, bk)
            assert code == 200

    def test_error_user_id(self):
        """测试不存在的用户ID"""
        book_id = self.books[0].id
        code = self.seller.add_stock_level(
            self.user_id + "_x", self.store_id, book_id, 10
        )
        assert code == 511  # 用户ID不存在

    def test_error_store_id(self):
        """测试不存在的商店ID"""
        book_id = self.books[0].id
        code = self.seller.add_stock_level(
            self.user_id, self.store_id + "_x", book_id, 10
        )
        assert code == 513  # 商店ID不存在

    def test_error_book_id(self):
        """测试不存在的图书ID"""
        book_id = self.books[0].id
        code = self.seller.add_stock_level(
            self.user_id, self.store_id, book_id + "_x", 10
        )
        assert code == 515  # 图书ID不存在

    def test_ok(self):
        """测试正常添加库存"""
        book_id = self.books[0].id
        code = self.seller.add_stock_level(
            self.user_id, self.store_id, book_id, 10
        )
        assert code == 200  # 成功添加库存
