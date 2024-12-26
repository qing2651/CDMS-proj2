from flask import Flask
from be.view import auth
from be.view import seller
from be.view import buyer
from be.model.store import init_database, init_completed_event
import os
import logging

def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__)
    
    # 初始化数据库
    parent_path = os.path.dirname(os.path.dirname(__file__))
    init_database(parent_path)
    
    # 配置日志
    log_file = os.path.join(parent_path, "app.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 注册蓝图
    app.register_blueprint(auth.bp_auth)
    app.register_blueprint(seller.bp_seller)
    app.register_blueprint(buyer.bp_buyer)
    
    # 设置初始化完成事件
    init_completed_event.set()
    
    return app

app = create_app()
