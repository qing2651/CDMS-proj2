import jwt
import time
import logging
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.exc import IntegrityError
from typing import Tuple, Optional
import bcrypt
from contextlib import contextmanager
from decimal import Decimal
from . import store
from .db_config import SessionLocal
from .store import User
from .error import error_authorization_fail, error_non_exist_user_id

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET = "your-secret-key"  # 在生产环境中应该使用环境变量
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 3600 * 24 * 7  # 7天

class UserManager:
    def __init__(self):
        self.token_lifetime = JWT_EXPIRATION_SECONDS
        self.db_conn = None

    def get_session(self, user_id: str, token: str) -> bool:
        """验证用户会话是否有效。

        Args:
            user_id (str): 用户ID
            token (str): 用户token

        Returns:
            bool: 如果会话有效返回True，否则返回False
        """
        try:
            logger.info(f"开始验证用户会话: user_id={user_id}")
            
            # 首先验证token的有效性
            valid, token_user_id = self._verify_token(token, user_id)
            if not valid:
                return False
                
            # 验证用户ID是否匹配
            if token_user_id != user_id:
                logger.warning(f"用户ID不匹配: token_user_id={token_user_id}, user_id={user_id}")
                return False
                
            logger.info(f"用户会话验证成功: user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"验证会话时发生错误: {str(e)}")
            return False

    def close_db(self):
        pass
        
    def register(self, user_id: str, password: str) -> Tuple[int, str, Optional[str]]:
        """
        注册新用户
        :param user_id: 用户ID
        :param password: 密码
        :return: (错误码，消息，token)
        """
        if not user_id or not password:
            logger.error("注册失败：用户ID或密码为空")
            return 1, "用户ID和密码不能为空", None

        try:
            with SessionLocal() as db:
                # 检查用户是否已存在
                existing_user = db.query(User).filter(User.user_id == user_id).first()
                if existing_user:
                    logger.warning(f"注册失败：用户已存在 (user_id={user_id})")
                    return 1, "用户已存在", None
                
                # 生成密码哈希
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
                
                # 生成token
                token = self._generate_token(user_id)
                
                # 创建新用户，设置默认余额
                new_user = User(
                    user_id=user_id,
                    username=user_id,  # 暂时用user_id作为username
                    password=hashed_password.decode('utf-8'),
                    balance=Decimal('1000000.00'),  # 设置默认余额
                    token=token  # 设置token
                )
                
                try:
                    db.add(new_user)
                    db.commit()
                    logger.info(f"用户注册成功: {user_id}")
                    return 0, "注册成功", token
                except IntegrityError:
                    db.rollback()
                    logger.warning(f"注册失败：数据库约束冲突 (user_id={user_id})")
                    return 1, "用户已存在", None
                except Exception as e:
                    db.rollback()
                    logger.error(f"注册失败：数据库操作错误 - {str(e)}")
                    return 530, f"注册失败：{str(e)}", None
                    
        except Exception as e:
            logger.error(f"注册过程发生未知错误: {str(e)}")
            return 530, f"注册失败：系统错误", None
            
    def _generate_token(self, user_id: str) -> str:
        """生成JWT token"""
        try:
            # 设置token的payload
            payload = {
                'user_id': user_id,
                'exp': int(time.time()) + self.token_lifetime,
                'iat': int(time.time())
            }
            # 生成token
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
            return token
        except Exception as e:
            logger.error(f"生成token失败: {str(e)}")
            raise

    def login(self, user_id: str, password: str) -> Tuple[int, str, Optional[str]]:
        """
        用户登录
        :param user_id: 用户ID
        :param password: 密码
        :return: (错误码，消息，token)
        """
        try:
            with SessionLocal() as db:
                # 查找用户
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return 1, "用户不存在", None

                # 验证密码
                if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                    return 2, "密码错误", None

                # 生成新token
                token = self._generate_token(user_id)
                user.token = token
                db.commit()

                return 0, "登录成功", token

        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            return 530, f"登录失败: {str(e)}", None

    def _verify_token(self, token: str, user_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        验证token的有效性
        :param token: JWT token
        :param user_id: 可选的用户ID，用于验证token是否属于该用户
        :return: (是否有效，token中的user_id)
        """
        try:
            logger.info(f"开始验证token: user_id={user_id}")
            
            if not token:
                logger.warning("token为空")
                return False, None
                
            # 解码token
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            except jwt.ExpiredSignatureError:
                logger.warning("token已过期")
                return False, None
            except jwt.InvalidTokenError as e:
                logger.warning(f"无效的token: {str(e)}")
                return False, None
                
            token_user_id = payload.get('user_id')
            if not token_user_id:
                logger.warning("token中缺少user_id")
                return False, None
                
            # 检查token是否过期
            exp = payload.get('exp')
            if exp is None:
                logger.warning("token中缺少过期时间")
                return False, None
                
            if int(time.time()) > exp:
                logger.warning("token已过期")
                return False, None
                
            # 如果提供了user_id，验证token是否属于该用户
            if user_id is not None and token_user_id != user_id:
                logger.warning(f"token不属于该用户: token_user_id={token_user_id}, user_id={user_id}")
                return False, None
                
            # 验证token是否在数据库中存在且有效
            with SessionLocal() as db:
                user = db.query(User).filter(
                    User.user_id == token_user_id,
                    User.token == token
                ).first()
                
                if not user:
                    logger.warning(f"数据库中未找到匹配的token: user_id={token_user_id}")
                    return False, None
                    
            logger.info(f"token验证成功: user_id={token_user_id}")
            return True, token_user_id
            
        except Exception as e:
            logger.error(f"验证token时发生错误: {str(e)}")
            return False, None
