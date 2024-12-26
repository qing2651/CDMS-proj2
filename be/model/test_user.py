import os
import sys
import pytest
import time
from sqlalchemy import text
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .user import UserManager
from .db_config import engine

class TestUser:
    @classmethod
    def setup_class(cls):
        """在所有测试开始前执行一次"""
        logger.info("开始测试用例执行...")
        cls.user = UserManager()
        cls.test_username = "test_user"
        cls.test_password = "test_password"
    
    @classmethod
    def teardown_class(cls):
        """在所有测试结束后执行一次"""
        cls.user.close_db()
        logger.info("测试用例执行完成")
    
    def test_register(self):
        logger.info("测试注册功能...")
        start_time = time.time()
        
        # 测试注册
        code, message, token = self.user.register(self.test_username, self.test_password)
        assert code == 0
        assert token is not None
        
        # 测试重复注册
        code, message, token = self.user.register(self.test_username, self.test_password)
        assert code == 1
        assert token is None
        
        logger.info(f"注册测试完成，耗时: {time.time() - start_time:.2f}秒")
    
    def test_login(self):
        logger.info("测试登录功能...")
        start_time = time.time()
        
        # 先注册
        self.user.register(f"{self.test_username}_login", self.test_password)
        
        # 测试正确登录
        code, message, token = self.user.login(f"{self.test_username}_login", self.test_password)
        assert code == 0
        assert token is not None
        
        # 测试错误密码
        code, message, token = self.user.login(f"{self.test_username}_login", "wrong_password")
        assert code == 2
        assert token is None
        
        # 测试不存在的用户
        code, message, token = self.user.login("non_exist_user", self.test_password)
        assert code == 1
        assert token is None
        
        logger.info(f"登录测试完成，耗时: {time.time() - start_time:.2f}秒")
    
    def test_logout(self):
        logger.info("测试登出功能...")
        start_time = time.time()
        
        # 先注册并登录
        self.user.register(f"{self.test_username}_logout", self.test_password)
        code, message, token = self.user.login(f"{self.test_username}_logout", self.test_password)
        
        # 测试正常登出
        code, message = self.user.logout(token)
        assert code == 0
        
        # 测试使用已登出的token
        code, message = self.user.logout(token)
        assert code == 1
        
        # 测试使用无效token
        code, message = self.user.logout("invalid_token")
        assert code == 1
        
        logger.info(f"登出测试完成，耗时: {time.time() - start_time:.2f}秒")
    
    def test_change_password(self):
        logger.info("测试修改密码功能...")
        start_time = time.time()
        
        # 先注册
        self.user.register(f"{self.test_username}_pwd", self.test_password)
        
        # 测试正常修改密码
        code, message = self.user.change_password(
            f"{self.test_username}_pwd", 
            self.test_password, 
            "new_password"
        )
        assert code == 0
        
        # 测试使用旧密码登录
        code, message, token = self.user.login(f"{self.test_username}_pwd", self.test_password)
        assert code == 2
        assert token is None
        
        # 测试使用新密码登录
        code, message, token = self.user.login(f"{self.test_username}_pwd", "new_password")
        assert code == 0
        assert token is not None
        
        # 测试使用错误的旧密码修改
        code, message = self.user.change_password(
            f"{self.test_username}_pwd",
            "wrong_old_password",
            "another_new_password"
        )
        assert code == 2
        
        # 测试不存在的用户
        code, message = self.user.change_password(
            "non_exist_user",
            self.test_password,
            "new_password"
        )
        assert code == 1
        
        logger.info(f"修改密码测试完成，耗时: {time.time() - start_time:.2f}秒")
    