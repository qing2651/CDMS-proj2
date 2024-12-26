import os

# 从环境变量获取端口，如果不存在则使用默认值5555
PORT = os.environ.get('BOOKSTORE_PORT', '5555')
URL = f"http://127.0.0.1:{PORT}/"

# Performance Test Configuration
Store_N = 2  # 每个卖家的商店数
Book_N = 5  # 每个商店的图书数
Seller_N = 2  # 卖家数量
Buyer_N = 10  # 买家数量

# Test Parameters
Session_N = 10  # 会话数
Request_N = 10  # 每个会话的请求数

# Business Configuration
Default_Stock_Level = 100  # 默认库存
Default_User_Funds = 10000  # 默认用户资金
Max_Books_Per_Store = 2000  # 每个商店最大图书数
Max_Stock_Level = 1000  # 最大库存数量
Order_Timeout = 900  # 订单超时时间（秒）

# Database Configuration
Use_Large_DB = False  # 是否使用大型数据库
Data_Batch_Size = 100  # 数据批量处理大小
DB_Host = os.environ.get('DB_HOST', 'localhost')
DB_Port = int(os.environ.get('DB_PORT', 3306))
DB_User = os.environ.get('DB_USER', 'root')
DB_Password = os.environ.get('DB_PASSWORD', '123456')
DB_Name = os.environ.get('DB_NAME', 'bookstore')

# Cache Configuration
Cache_Size = 1000  # 缓存大小
Cache_Expire = 3600  # 缓存过期时间（秒）

# API Rate Limits
Rate_Limit = 100  # 每分钟请求限制
Rate_Limit_Window = 60  # 限制窗口（秒）

# Book Price Configuration
Min_Book_Price = 1  # 最低图书价格
Max_Book_Price = 1000  # 最高图书价格
Default_Book_Price = 10  # 默认图书价格
