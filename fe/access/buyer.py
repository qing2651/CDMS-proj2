import requests
import simplejson
from urllib.parse import urljoin
from fe.access.auth import Auth


class Buyer:
    def __init__(self, url_prefix, user_id, password):
        self.url_prefix = urljoin(url_prefix, "buyer/")
        self.user_id = user_id
        self.password = password
        self.token = ""
        self.auth = Auth(url_prefix)
        code, self.token = self.auth.login(user_id, password, "")
        assert code == 200

    def new_order(self, store_id: str, book_id_and_count: [(str, int)]) -> (int, str):
        books = []
        for book_id, count in book_id_and_count:
            books.append({"id": book_id, "count": count})
        json = {
            "user_id": self.user_id,
            "store_id": store_id,
            "books": books
        }
        url = urljoin(self.url_prefix, "new_order")
        headers = self.auth.get_headers(self.user_id, self.token)
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return r.status_code, response_json.get("order_id", "")

    def payment(self, order_id: str) -> int:
        json = {
            "user_id": self.user_id,
            "order_id": order_id,
            "password": self.password
        }
        url = urljoin(self.url_prefix, "payment")
        headers = self.auth.get_headers(self.user_id, self.token)
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_funds(self, add_value: str) -> int:
        json = {
            "user_id": self.user_id,
            "password": self.password,
            "add_value": add_value
        }
        url = urljoin(self.url_prefix, "add_funds")
        headers = self.auth.get_headers(self.user_id, self.token)
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def receive(self, order_id: str) -> int:
        """确认收货"""
        json = {
            "user_id": self.user_id,
            "order_id": order_id
        }
        url = urljoin(self.url_prefix, "receive")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def search_books(self, keyword: str, page: int = 1, per_page: int = 10, sort_by: str = None, store_id: str = None, search_type: str = "normal") -> dict:
        """搜索图书
        :param keyword: 搜索关键词
        :param page: 页码（从1开始）
        :param per_page: 每页数量
        :param sort_by: 排序方式（price_asc, price_desc, title_asc, title_desc）
        :param store_id: 商店ID（None表示全站搜索）
        :param search_type: 搜索类型（normal: 普通搜索, fulltext: 全文搜索）
        """
        params = {
            "keyword": keyword,
            "page": page,
            "per_page": per_page,
            "search_type": search_type
        }
        if sort_by:
            params["sort_by"] = sort_by
        if store_id:
            params["store_id"] = store_id
            
        url = urljoin(self.url_prefix, "search")
        headers = {"token": self.token}
        r = requests.get(url, headers=headers, params=params)
        return r.json()

    def cancel_order(self, order_id: str) -> int:
        """取消订单"""
        json = {
            "user_id": self.user_id,
            "order_id": order_id
        }
        url = urljoin(self.url_prefix, "cancel")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code
