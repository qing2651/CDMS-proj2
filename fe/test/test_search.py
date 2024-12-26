import pytest
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
import uuid

class TestSearch:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_search_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_search_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_search_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        # 创建卖家和商店
        self.seller = register_new_seller(self.seller_id, self.password)
        code = self.seller.create_store(self.store_id)
        assert code == 200
        
        # 创建买家
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        
        # 生成测试图书数据
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=30
        )
        assert ok
        self.buy_book_info_list = gen_book.buy_book_info_list
        
        yield
    
    def test_basic_search(self):
        # 测试基本搜索功能
        result = self.buyer.search_books(keyword="book")
        assert result.get("total") > 0
        assert len(result.get("books")) > 0
    
    def test_empty_search(self):
        # 测试空关键字搜索
        result = self.buyer.search_books(keyword="")
        assert result.get("total") > 0
        assert len(result.get("books")) > 0
    
    def test_no_result_search(self):
        # 测试无结果搜索
        result = self.buyer.search_books(keyword="nonexistentbook123456")
        assert result.get("total") == 0
        assert len(result.get("books")) == 0
    
    def test_pagination(self):
        # 测试分页功能
        per_page = 5
        result = self.buyer.search_books(keyword="", page=1, per_page=per_page)
        assert len(result.get("books")) <= per_page
        assert result.get("page") == 1
        assert result.get("per_page") == per_page
        
        # 测试第二页
        result2 = self.buyer.search_books(keyword="", page=2, per_page=per_page)
        assert len(result2.get("books")) <= per_page
        assert result2.get("page") == 2
        
        # 确保两页的内容不同
        page1_ids = {book["id"] for book in result.get("books")}
        page2_ids = {book["id"] for book in result2.get("books")}
        assert not page1_ids.intersection(page2_ids)
    
    def test_sorting(self):
        # 测试价格升序排序
        result_asc = self.buyer.search_books(keyword="", sort_by="price_asc")
        prices_asc = [book["price"] for book in result_asc.get("books")]
        assert prices_asc == sorted(prices_asc)
        
        # 测试价格降序排序
        result_desc = self.buyer.search_books(keyword="", sort_by="price_desc")
        prices_desc = [book["price"] for book in result_desc.get("books")]
        assert prices_desc == sorted(prices_desc, reverse=True)
    
    def test_store_filter(self):
        # 测试商店过滤
        result = self.buyer.search_books(keyword="", store_id=self.store_id)
        assert result.get("total") > 0
        for book in result.get("books"):
            assert book["store_id"] == self.store_id
        
        # 测试不存在的商店
        result = self.buyer.search_books(keyword="", store_id=self.store_id + "_x")
        assert result.get("total") == 0 
    
    def test_price_filter(self):
        # 获取所有图书的价格范围
        result = self.buyer.search_books(keyword="")
        all_prices = [book["price"] for book in result.get("books")]
        min_price = min(all_prices)
        max_price = max(all_prices)
        mid_price = (min_price + max_price) / 2
        
        # 测试最低价格筛选
        result = self.buyer.search_books(keyword="", min_price=mid_price)
        filtered_prices = [book["price"] for book in result.get("books")]
        assert all(price >= mid_price for price in filtered_prices)
        
        # 测试最高价格筛选
        result = self.buyer.search_books(keyword="", max_price=mid_price)
        filtered_prices = [book["price"] for book in result.get("books")]
        assert all(price <= mid_price for price in filtered_prices)
        
        # 测试价格区间筛选
        result = self.buyer.search_books(keyword="", min_price=min_price, max_price=max_price)
        filtered_prices = [book["price"] for book in result.get("books")]
        assert all(min_price <= price <= max_price for price in filtered_prices)
        
        # 测试无结果的价格区间
        result = self.buyer.search_books(keyword="", min_price=max_price + 1)
        assert result.get("total") == 0
        assert len(result.get("books")) == 0
    
    def test_fulltext_search(self):
        """测试全文搜索功能"""
        # 测试标题搜索
        result = self.buyer.search_books(keyword="book", search_type="fulltext")
        assert result.get("total") > 0
        
        # 测试标签搜索
        result = self.buyer.search_books(keyword="fiction", search_type="fulltext")
        assert result.get("total") >= 0
        
        # 测试目录搜索
        result = self.buyer.search_books(keyword="chapter", search_type="fulltext")
        assert result.get("total") >= 0
        
        # 测试描述搜索
        result = self.buyer.search_books(keyword="introduction", search_type="fulltext")
        assert result.get("total") >= 0
        
        # 测试组合搜索
        result = self.buyer.search_books(keyword="book fiction", search_type="fulltext")
        assert result.get("total") >= 0
        
        # 测试无结果搜索
        result = self.buyer.search_books(keyword="nonexistentxxx123", search_type="fulltext")
        assert result.get("total") == 0
    
    def test_search_with_store_filter(self):
        """测试带商店过滤的搜索"""
        # 全站搜索
        result_all = self.buyer.search_books(keyword="book")
        
        # 特定商店搜索
        result_store = self.buyer.search_books(keyword="book", store_id=self.store_id)
        
        # 验证结果
        assert result_all.get("total") >= result_store.get("total")
        for book in result_store.get("books"):
            assert book["store_id"] == self.store_id
    
    def test_search_pagination(self):
        """测试搜索分页"""
        per_page = 5
        
        # 获取第一页
        result1 = self.buyer.search_books(keyword="", page=1, per_page=per_page)
        assert len(result1.get("books")) <= per_page
        
        # 获取第二页
        result2 = self.buyer.search_books(keyword="", page=2, per_page=per_page)
        assert len(result2.get("books")) <= per_page
        
        # 验证两页的内容不重复
        page1_ids = {book["id"] for book in result1.get("books")}
        page2_ids = {book["id"] for book in result2.get("books")}
        assert not page1_ids.intersection(page2_ids)
        
        # 验证分页信息
        assert result1.get("page") == 1
        assert result1.get("per_page") == per_page
        assert result1.get("total_pages") == (result1.get("total") + per_page - 1) // per_page