"""
数据库索引关系定义
"""

# 主键索引定义
PRIMARY_KEYS = {
    "user": "id",
    "order": "id",
    "new_order": "id",
    "user_store": "id",
    "store_book": "id",
    "books": "id",
    "order_detail": "id",
    "payment": "id"
}

# 唯一索引定义
UNIQUE_INDICES = {
    "user": ["user_id"],
    "order": ["order_id"],
    "new_order": ["order_id"],
    "user_store": ["store_id"],
    "books": ["book_id"],
    "store_book": [("store_id", "book_id")],  # 复合唯一索引
    "payment": ["order_id"]
}

# 外键关系定义
FOREIGN_KEYS = {
    "order": {
        "user_id": ("user", "user_id")
    },
    "new_order": {
        "user_id": ("user", "user_id"),
        "order_id": ("order", "order_id")
    },
    "user_store": {
        "user_id": ("user", "user_id")
    },
    "order_detail": {
        "order_id": ("order", "order_id")
    },
    "payment": {
        "order_id": ("order", "order_id"),
        "user_id": ("user", "user_id")
    }
}

# 普通索引定义
NORMAL_INDICES = {
    "user": ["token"],
    "order": ["user_id", "store_id", "time"],
    "user_store": ["user_id"],
    "store_book": ["store_id", "book_id"],
    "books": ["title", "isbn"],
    "order_detail": ["order_id", "book_id"],
    "payment": ["user_id", "time"]
}

# 表关系定义
TABLE_RELATIONS = {
    "user": {
        "children": ["order", "new_order", "user_store", "payment"]
    },
    "order": {
        "children": ["order_detail", "new_order", "payment"],
        "parents": ["user"]
    },
    "new_order": {
        "parents": ["user", "order"]
    },
    "user_store": {
        "children": ["store_book"],
        "parents": ["user"]
    },
    "store_book": {
        "children": ["books"],
        "parents": ["user_store"]
    },
    "books": {
        "parents": ["store_book"]
    },
    "order_detail": {
        "parents": ["order"]
    },
    "payment": {
        "parents": ["user", "order"]
    }
}

# 查询优化说明
QUERY_OPTIMIZATION = {
    "user_queries": {
        "find_by_user_id": "通过user_id快速查找用户信息",
        "verify_by_token": "通过token快速验证用户身份"
    },
    "order_queries": {
        "find_by_user": "通过user_id查找用户的所有订单",
        "find_by_store": "通过store_id查找店铺的所有订单",
        "find_by_time_range": "通过时间范围查询订单"
    },
    "store_queries": {
        "find_product": "通过store_id和book_id快速定位商品",
        "find_seller_stores": "通过user_id查找卖家的所有商店"
    },
    "book_queries": {
        "find_by_id": "通过book_id快速查找图书信息",
        "search": "通过title和isbn进行图书搜索"
    },
    "payment_queries": {
        "find_by_order": "通过order_id查找支付信息",
        "find_by_user": "通过user_id查找用户的所有支付记录",
        "find_by_time": "通过时间范围查询支付记录"
    }
}

def get_table_indices(table_name: str) -> dict:
    """获取指定表的所有索引信息"""
    return {
        "primary_key": PRIMARY_KEYS.get(table_name),
        "unique_indices": UNIQUE_INDICES.get(table_name, []),
        "foreign_keys": FOREIGN_KEYS.get(table_name, {}),
        "normal_indices": NORMAL_INDICES.get(table_name, [])
    }

def get_table_relations(table_name: str) -> dict:
    """获取指定表的关系信息"""
    return TABLE_RELATIONS.get(table_name, {})

def get_query_optimization(query_type: str) -> dict:
    """获取指定查询类型的优化信息"""
    return QUERY_OPTIMIZATION.get(query_type, {}) 