import requests
import threading
import time
import pytest
from urllib.parse import urljoin
from be import serve
from fe import conf

thread: threading.Thread = None


def wait_for_server(url: str, timeout: float = 10) -> bool:
    """等待服务器启动"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 404:  # Flask返回404表示服务器在运行
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(0.1)
            continue
    return False


@pytest.fixture(autouse=True)
def run_server():
    """启动服务器"""
    global thread
    
    # 如果服务器已经在运行，就不需要再启动了
    if thread is not None and thread.is_alive():
        return
    
    # 启动服务器
    thread = threading.Thread(target=serve.be_run)
    thread.daemon = True
    thread.start()
    
    # 等待服务器启动
    url = urljoin(conf.URL, "")  # 使用根路径检查服务器状态
    assert wait_for_server(url), "服务器启动失败"
    
    yield
    
    # 清理服务器
    requests.get(urljoin(conf.URL, "shutdown"))
