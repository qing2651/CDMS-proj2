import pytest
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def pytest_collection_modifyitems(session, config, items):
    """修改测试项目的收集方式"""
    logger.info(f"收集到 {len(items)} 个测试用例")
    for item in items:
        logger.info(f"测试用例: {item.name}")

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """设置测试环境，确保所有测试使用同一个服务器实例"""
    logger.info("开始设置测试环境...")
    
    # 检查环境变量中是否已有端口号
    port = os.environ.get('BOOKSTORE_PORT')
    if not port:
        logger.error("环境变量中未找到BOOKSTORE_PORT，请确保服务器已启动")
        raise RuntimeError("Server port not found in environment variables")
    
    logger.info(f"使用已存在的服务器实例，端口: {port}")
    yield
    
    logger.info("测试环境清理完成")