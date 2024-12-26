import logging
import os
import socket
import traceback
from flask import Flask, Blueprint, request
from bookstore.be.view import auth
from bookstore.be.view import seller
from bookstore.be.view import buyer
from bookstore.be.model.db_config import clean_db
from bookstore.be.model.buyer import BuyerManager
import threading
import time

# 配置日志
logger = logging.getLogger(__name__)

# 全局变量存储当前使用的端口
current_port = None
server_ready = threading.Event()

bp_shutdown = Blueprint("shutdown", __name__)

def find_free_port():
    """查找可用的端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port

def get_current_port():
    """获取当前使用的端口"""
    global current_port, server_ready
    if server_ready.wait(timeout=10):  # 增加等待时间到10秒
        return current_port
    return None

def shutdown_server():
    """关闭服务器"""
    try:
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
    except Exception as e:
        logger.error(f"关闭服务器失败: {str(e)}")
        # 强制退出
        os._exit(0)

@bp_shutdown.route("/shutdown")
def be_shutdown():
    """关闭服务器的路由"""
    logger.info("正在关闭服务器...")
    try:
        shutdown_server()
        return "Server shutting down..."
    except Exception as e:
        logger.error(f"关闭服务器失败: {str(e)}")
        return "Server shutdown failed", 500

def check_expired_orders():
    """定时检查过期订单的线程函数"""
    buyer_manager = BuyerManager()
    while True:
        try:
            # 每分钟检查一次
            time.sleep(60)
            cancelled_count = buyer_manager.check_expired_orders()
            if cancelled_count > 0:
                logger.info(f"定时任务取消了 {cancelled_count} 个过期订单")
        except Exception as e:
            logger.error(f"检查过期订单时出错: {str(e)}")

def be_run():
    """运行服务器"""
    global current_port, server_ready
    
    # 重置服务器就绪状态
    server_ready.clear()
    current_port = None
    
    # 打印调用栈，追踪启动来源
    logger.info("服务器启动调用栈:")
    for line in traceback.format_stack():
        logger.info(line.strip())
    
    logger.info("正在启动服务器...")
    this_path = os.path.dirname(__file__)
    parent_path = os.path.dirname(this_path)
    log_file = os.path.join(parent_path, "app.log")

    # 配置日志
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s'
    )
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    # 创建应用
    logger.info("创建Flask应用...")
    app = Flask(__name__)
    
    # 注册蓝图
    logger.info("注册蓝图...")
    app.register_blueprint(bp_shutdown)
    app.register_blueprint(auth.bp_auth)
    app.register_blueprint(seller.bp_seller)
    app.register_blueprint(buyer.bp_buyer)
    
    # 查找可用端口
    current_port = find_free_port()
    logger.info(f"使用端口: {current_port}")
    
    # 设置服务器就绪事件
    server_ready.set()
    
    # 导入基础数据
    logger.info("导入基础数据...")
    try:
        from .model.migrate_data import migrate_sqlite_to_mysql
        if migrate_sqlite_to_mysql():
            logger.info("基础数据导入成功")
        else:
            logger.warning("基础数据导入失败，可能影响部分功能")
    except Exception as e:
        logger.error(f"导入基础数据失败: {str(e)}")
        raise
    
    # 启动过期订单检查线程
    expire_checker = threading.Thread(target=check_expired_orders, name="ExpireChecker")
    expire_checker.daemon = True
    expire_checker.start()
    logger.info("过期订单检查线程已启动")
    
    # 启动服务器
    logger.info(f"启动服务器在端口 {current_port}...")
    app.run(host='127.0.0.1', port=current_port, threaded=True)

if __name__ == "__main__":
    be_run()
