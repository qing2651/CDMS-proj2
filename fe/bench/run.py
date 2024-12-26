import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fe.bench.workload import Workload
from fe.bench.session import Session

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bench(max_workers=2, timeout=60):
    """
    运行性能测试
    :param max_workers: 最大并发线程数
    :param timeout: 超时时间（秒）
    """
    start_time = time.time()
    logger.info("初始化性能测试...")
    
    try:
        # 初始化工作负载
        wl = Workload()
        logger.info("生成测试数据...")
        wl.gen_database()
        
        # 创建会话
        sessions = []
        for i in range(0, min(wl.session, max_workers)):
            ss = Session(wl)
            sessions.append(ss)
        
        logger.info(f"创建了 {len(sessions)} 个测试会话")
        
        # 使用线程池并发执行会话
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_session = {
                executor.submit(session.run): session 
                for session in sessions
            }
            
            # 等待所有任务完成或超时
            completed = 0
            for future in as_completed(future_to_session, timeout=timeout):
                session = future_to_session[future]
                try:
                    result = future.result()
                    completed += 1
                    logger.info(f"会话 {completed}/{len(sessions)} 完成")
                except Exception as e:
                    logger.error(f"会话执行失败: {str(e)}")
        
        # 计算总耗时
        total_time = time.time() - start_time
        logger.info(f"性能测试完成，总耗时: {total_time:.2f}秒")
        
        # 验证所有会话是否成功完成
        if completed != len(sessions):
            raise Exception(f"只有 {completed}/{len(sessions)} 个会话成功完成")
            
    except Exception as e:
        logger.error(f"性能测试失败: {str(e)}")
        raise


# if __name__ == "__main__":
#    run_bench()
