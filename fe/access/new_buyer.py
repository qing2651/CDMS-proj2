from fe.access.auth import Auth
from fe.access.buyer import Buyer
from fe import conf
import logging

logger = logging.getLogger(__name__)

def register_new_buyer(user_id: str, password: str) -> Buyer:
    """
    注册新买家，并设置默认余额
    :param user_id: 用户ID
    :param password: 密码
    :return: Buyer对象
    """
    auth = Auth(conf.URL)
    
    # 注册
    code = auth.register(user_id, password)
    if code != 200:
        raise Exception(f"注册失败，状态码：{code}")
    
    # 创建买家对象
    buyer = Buyer(conf.URL, user_id, password)
    
    # 设置默认余额
    code = buyer.add_funds(conf.Default_User_Funds)
    if code != 200:
        logger.warning(f"设置默认余额失败，状态码：{code}")
    
    return buyer
