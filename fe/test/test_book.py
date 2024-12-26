import pytest
from bookstore.fe.access.book import Book, BookDB
from sqlalchemy import create_engine, text
import os

class TestBook:
    @pytest.fixture(autouse=True)
    def setup_class(self):
        self.book_db = BookDB()
        yield
    
    def test_book_init(self):
        """测试 Book 类的初始化"""
        book = Book()
        assert book.tags == []
        assert book.pictures == []
        assert book.stock == 0
        assert book.original_price == 0.0
    
    def test_init_test_data(self):
        """测试数据初始化功能"""
        # 确保测试数据被正确初始化
        book_count = self.book_db.get_book_count()
        assert book_count == 3  # 应该有3本测试图书
        
        # 获取并验证图书信息
        books = self.book_db.get_book_info(0, 3)
        assert len(books) == 3
        
        # 验证第一本书的信息
        first_book = books[0]
        assert first_book.id == 'test_book_1'
        assert first_book.price == 45.00
        assert first_book.stock == 100
    
    def test_get_book_count(self):
        """测试图书数量统计功能"""
        count = self.book_db.get_book_count()
        assert count == 3  # 应该有3本测试图书
    
    def test_get_book_info_pagination(self):
        """测试图书信息分页查询功能"""
        # 测试第一页
        books = self.book_db.get_book_info(0, 2)
        assert len(books) == 2
        assert books[0].id == 'test_book_1'
        assert books[1].id == 'test_book_2'
        
        # 测试第二页
        books = self.book_db.get_book_info(2, 2)
        assert len(books) == 1
        assert books[0].id == 'test_book_3'
        
        # 测试超出范围的页
        books = self.book_db.get_book_info(4, 2)
        assert len(books) == 0
    
    def test_get_book_info_invalid_params(self):
        """测试无效的分页参数"""
        # 测试负数起始位置
        books = self.book_db.get_book_info(-1, 2)
        assert len(books) == 0
        
        # 测试零或负数页大小
        books = self.book_db.get_book_info(0, 0)
        assert len(books) == 0
        books = self.book_db.get_book_info(0, -1)
        assert len(books) == 0 