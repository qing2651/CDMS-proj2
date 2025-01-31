import requests
from urllib.parse import urljoin


class Auth:
    def __init__(self, url_prefix):
        self.url_prefix = urljoin(url_prefix, "auth/")

    def login(self, user_id: str, password: str, terminal: str) -> (int, str):
        json = {
            "user_id": user_id,
            "password": password,
            "terminal": terminal,
        }
        url = urljoin(self.url_prefix, "login")
        r = requests.post(url, json=json)
        return r.status_code, r.json().get("token", "")

    def register(self, user_id: str, password: str) -> int:
        json = {
            "user_id": user_id,
            "password": password,
        }
        url = urljoin(self.url_prefix, "register")
        r = requests.post(url, json=json)
        return r.status_code

    def password(self, user_id: str, old_password: str, new_password: str) -> int:
        json = {
            "user_id": user_id,
            "oldPassword": old_password,
            "newPassword": new_password,
        }
        url = urljoin(self.url_prefix, "password")
        r = requests.post(url, json=json)
        return r.status_code

    def get_headers(self, user_id: str, token: str) -> dict:
        """生成包含认证信息的请求头"""
        return {
            "user_id": user_id,
            "token": token
        }

    def logout(self, user_id: str, token: str) -> int:
        json = {
            "user_id": user_id,
        }
        url = urljoin(self.url_prefix, "logout")
        headers = self.get_headers(user_id, token)
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def unregister(self, user_id: str, password: str) -> int:
        json = {
            "user_id": user_id,
            "password": password,
        }
        url = urljoin(self.url_prefix, "unregister")
        r = requests.post(url, json=json)
        return r.status_code
