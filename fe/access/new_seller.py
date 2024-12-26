from fe.access.auth import Auth
from fe.access.seller import Seller
from fe import conf

def register_new_seller(user_id: str, password: str) -> Seller:
    """
    注册新卖家
    :param user_id: 用户ID
    :param password: 密码
    :return: Seller对象
    """
    auth = Auth(conf.URL)
    # 注册
    code = auth.register(user_id, password)
    assert code == 200
    # 创建卖家对象
    seller = Seller(conf.URL, user_id, password)
    return seller
