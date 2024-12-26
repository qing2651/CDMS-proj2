import requests
from urllib.parse import urljoin
from fe.access.auth import Auth


class Seller:
    def __init__(self, url_prefix, user_id, password):
        self.url_prefix = urljoin(url_prefix, "seller/")
        self.user_id = user_id
        self.password = password
        self.terminal = "my terminal"
        self.auth = Auth(url_prefix)
        self.token = None

    def login(self):
        """登录卖家账户"""
        code, token = self.auth.login(self.user_id, self.password, self.terminal)
        self.token = token
        return code

    def create_store(self, store_id):
        """创建商店"""
        if not self.token:
            return 401
            
        json = {
            "user_id": self.user_id,
            "store_id": store_id,
        }
        url = urljoin(self.url_prefix, "create_store")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_book(self, store_id, book_id, price, stock_level):
        """添加图书"""
        if not self.token:
            return 401
            
        json = {
            "user_id": self.user_id,
            "store_id": store_id,
            "book_id": book_id,
            "price": price,
            "stock_level": stock_level
        }
        url = urljoin(self.url_prefix, "add_book")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int) -> int:
        """增加库存"""
        if not self.token:
            return 401
            
        json = {
            "user_id": user_id,
            "store_id": store_id,
            "book_id": book_id,
            "add_stock_level": add_stock_level
        }
        url = urljoin(self.url_prefix, "add_stock_level")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def deliver(self, order_id: str) -> int:
        """发货"""
        if not self.token:
            return 401
            
        json = {
            "user_id": self.user_id,
            "order_id": order_id
        }
        url = urljoin(self.url_prefix, "deliver")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code
