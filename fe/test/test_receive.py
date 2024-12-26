import pytest
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
import uuid

class TestReceive:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_receive_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_receive_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_receive_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        # 创建卖家和商店
        self.seller = register_new_seller(self.seller_id, self.password)
        self.seller.create_store(self.store_id)
        
        # 创建买家
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        
        # 生成测试图书数据
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        assert ok
        self.buy_book_info_list = gen_book.buy_book_info_list
        
        # 买家下单并付款
        code, self.order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        # 计算订单总价并充值
        self.total_price = 0
        for item in self.buy_book_info_list:
            book = item[0]
            num = item[1]
            if book.price is not None:
                self.total_price += book.price * num
        
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        
        # 卖家发货
        code = self.seller.deliver(self.order_id)
        assert code == 200
        
        yield
    
    def test_ok(self):
        # 测试正常收货
        code = self.buyer.receive(self.order_id)
        assert code == 200
    
    def test_non_exist_order_id(self):
        # 测试不存在的订单ID
        code = self.buyer.receive(self.order_id + "_x")
        assert code != 200
    
    def test_non_exist_user_id(self):
        # 测试不存在的用户ID
        self.buyer.user_id = self.buyer.user_id + "_x"
        code = self.buyer.receive(self.order_id)
        assert code != 200
    
    def test_authorization_error(self):
        # 测试未授权用户（非订单买家）
        other_buyer = register_new_buyer(self.buyer_id + "_x", self.password)
        code = other_buyer.receive(self.order_id)
        assert code != 200
    
    def test_wrong_order_status(self):
        # 测试错误的订单状态（已收货的订单不能重复收货）
        code = self.buyer.receive(self.order_id)
        assert code == 200
        code = self.buyer.receive(self.order_id)
        assert code != 200 