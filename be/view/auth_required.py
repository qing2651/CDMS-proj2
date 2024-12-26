from functools import wraps
from flask import request, jsonify
from bookstore.be.model.user import UserManager
from bookstore.be.model.error import error_non_exist_user_id
import logging

logger = logging.getLogger(__name__)

def auth_required(func):
    """统一的认证装饰器，用于验证用户身份"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 1. 获取认证信息
        user_id = request.headers.get('user_id')
        token = request.headers.get('token')
        
        if not user_id or not token:
            logger.warning("缺少认证信息: user_id或token为空")
            return jsonify({
                "code": 401,
                "message": "缺少认证信息",
                "details": "请提供user_id和token"
            }), 401
        
        try:
            # 2. 验证用户会话
            user_manager = UserManager()
            if not user_manager.get_session(user_id, token):
                logger.warning(f"认证失败: user_id={user_id}")
                return jsonify({
                    "code": 401,
                    "message": "认证失败",
                    "details": "无效的token或用户不存在"
                }), 401
            
            # 3. 执行被装饰的函数
            return func(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"认证过程发生错误: {str(e)}")
            return jsonify({
                "code": 500,
                "message": "服务器内部错误",
                "details": str(e)
            }), 500
    
    return wrapper 