import pytest
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
import uuid
import time


class TestNewOrder:
    @classmethod
    def setup_class(cls):
        # 类级别的设置，只执行一次
        cls.seller_id = "test_new_order_seller_id_{}".format(str(uuid.uuid1()))
        cls.store_id = "test_new_order_store_id_{}".format(str(uuid.uuid1()))
        cls.password = cls.seller_id
        
        # 使用正确的方式注册卖家
        cls.seller = register_new_seller(cls.seller_id, cls.password)
        cls.gen_book = GenBook(cls.seller_id, cls.store_id)

    def setup_method(self, method):
        # 方法级别的设置，每个测试方法执行前都会运行
        self.buyer_id = "test_new_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.buyer = register_new_buyer(self.buyer_id, self.password)

    def test_non_exist_book_id(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=True, low_stock_level=False
        )
        assert ok
        code, _ = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 515

    def test_low_stock_level(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=True
        )
        assert ok
        code, _ = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 517

    def test_ok(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, _ = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200

    def test_non_exist_user_id(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        self.buyer.user_id = self.buyer.user_id + "_x"
        code, _ = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 511

    def test_non_exist_store_id(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, _ = self.buyer.new_order(self.store_id + "_x", buy_book_id_list)
        assert code == 513

    def test_order_auto_cancel(self):
        """测试订单自动取消功能"""
        # 创建订单
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 等待订单过期（这里等待31分钟）
        time.sleep(31 * 60)
        
        # 尝试支付已过期订单
        code = self.buyer.payment(order_id)
        assert code != 200  # 应该支付失败
