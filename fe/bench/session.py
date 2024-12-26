import logging
import time
from fe.bench.workload import Workload, NewOrder, Payment

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Session:
    def __init__(self, wl: Workload):
        self.workload = wl
        self.new_order_request = []
        self.payment_request = []
        self.payment_i = 0
        self.new_order_i = 0
        self.payment_ok = 0
        self.new_order_ok = 0
        self.time_new_order = 0
        self.time_payment = 0
        self.gen_procedure()

    def gen_procedure(self):
        """生成测试过程"""
        try:
            for i in range(0, self.workload.procedure_per_session):
                new_order = self.workload.get_new_order()
                self.new_order_request.append(new_order)
            logger.debug(f"生成了 {len(self.new_order_request)} 个订单请求")
        except Exception as e:
            logger.error(f"生成测试过程失败: {str(e)}")
            raise

    def run(self):
        """运行测试会话"""
        try:
            batch_size = 10  # 每批处理的订单数
            total_orders = len(self.new_order_request)
            
            for i in range(0, total_orders, batch_size):
                # 处理一批订单
                batch = self.new_order_request[i:min(i + batch_size, total_orders)]
                self._process_order_batch(batch)
                
                # 处理积累的支付请求
                if len(self.payment_request) >= batch_size or i + batch_size >= total_orders:
                    self._process_payment_batch()
                
                # 更新统计信息
                self._update_stats()
                
            # 处理剩余的支付请求
            if self.payment_request:
                self._process_payment_batch()
                self._update_stats()
                
            return True
            
        except Exception as e:
            logger.error(f"运行测试会话失败: {str(e)}")
            return False

    def _process_order_batch(self, batch):
        """处理一批订单"""
        for new_order in batch:
            try:
                before = time.time()
                ok, order_id = new_order.run()
                after = time.time()
                
                self.time_new_order += after - before
                self.new_order_i += 1
                
                if ok:
                    self.new_order_ok += 1
                    payment = Payment(new_order.buyer, order_id)
                    self.payment_request.append(payment)
                    
            except Exception as e:
                logger.error(f"处理订单失败: {str(e)}")

    def _process_payment_batch(self):
        """处理积累的支付请求"""
        for payment in self.payment_request:
            try:
                before = time.time()
                ok = payment.run()
                after = time.time()
                
                self.time_payment += after - before
                self.payment_i += 1
                
                if ok:
                    self.payment_ok += 1
                    
            except Exception as e:
                logger.error(f"处理支付失败: {str(e)}")
                
        self.payment_request = []  # 清空已处理的支付请求

    def _update_stats(self):
        """更新统计信息"""
        try:
            self.workload.update_stat(
                self.new_order_i,
                self.payment_i,
                self.new_order_ok,
                self.payment_ok,
                self.time_new_order,
                self.time_payment,
            )
        except Exception as e:
            logger.error(f"更新统计信息失败: {str(e)}")
