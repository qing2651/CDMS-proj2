"""
初始化数据库索引
"""

import logging
from sqlalchemy import create_engine, text
from be.model.db_indices import (
    PRIMARY_KEYS,
    UNIQUE_INDICES,
    FOREIGN_KEYS,
    NORMAL_INDICES
)
from fe import conf

logger = logging.getLogger(__name__)

def init_database_indices():
    """初始化数据库索引"""
    try:
        # 创建数据库连接
        engine = create_engine(
            f'mysql+pymysql://{conf.DB_User}:{conf.DB_Password}@{conf.DB_Host}:{conf.DB_Port}/{conf.DB_Name}'
        )
        connection = engine.connect()

        # 创建唯一索引
        for table, indices in UNIQUE_INDICES.items():
            for index in indices:
                if isinstance(index, tuple):
                    # 处理复合索引
                    index_name = f"idx_unique_{'_'.join(index)}"
                    columns = ', '.join(index)
                    sql = f"""
                    CREATE UNIQUE INDEX IF NOT EXISTS {index_name}
                    ON {table} ({columns});
                    """
                else:
                    # 处理单列索引
                    index_name = f"idx_unique_{index}"
                    sql = f"""
                    CREATE UNIQUE INDEX IF NOT EXISTS {index_name}
                    ON {table} ({index});
                    """
                try:
                    connection.execute(text(sql))
                    logger.info(f"创建唯一索引成功: {index_name} on {table}")
                except Exception as e:
                    logger.error(f"创建唯一索引失败: {index_name} - {str(e)}")

        # 创建外键索引
        for table, fks in FOREIGN_KEYS.items():
            for column, (ref_table, ref_column) in fks.items():
                fk_name = f"fk_{table}_{column}"
                sql = f"""
                ALTER TABLE {table}
                ADD CONSTRAINT IF NOT EXISTS {fk_name}
                FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column});
                """
                try:
                    connection.execute(text(sql))
                    logger.info(f"创建外键成功: {fk_name}")
                except Exception as e:
                    logger.error(f"创建外键失败: {fk_name} - {str(e)}")

        # 创建普通索引
        for table, indices in NORMAL_INDICES.items():
            for index in indices:
                index_name = f"idx_{table}_{index}"
                sql = f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table} ({index});
                """
                try:
                    connection.execute(text(sql))
                    logger.info(f"创建普通索引成功: {index_name}")
                except Exception as e:
                    logger.error(f"创建普通索引失败: {index_name} - {str(e)}")

        connection.close()
        logger.info("数据库索引初始化完成")
        return True

    except Exception as e:
        logger.error(f"初始化数据库索引失败: {str(e)}")
        return False

def check_indices():
    """检查数据库索引状态"""
    try:
        engine = create_engine(
            f'mysql+pymysql://{conf.DB_User}:{conf.DB_Password}@{conf.DB_Host}:{conf.DB_Port}/{conf.DB_Name}'
        )
        connection = engine.connect()

        # 获取所有表的索引信息
        sql = """
        SELECT 
            TABLE_NAME,
            INDEX_NAME,
            COLUMN_NAME,
            NON_UNIQUE
        FROM 
            information_schema.STATISTICS 
        WHERE 
            TABLE_SCHEMA = :db_name
        ORDER BY 
            TABLE_NAME, INDEX_NAME;
        """
        
        result = connection.execute(text(sql), {"db_name": conf.DB_Name})
        indices = result.fetchall()
        
        # 检查并报告索引状态
        index_status = {}
        for index in indices:
            table_name = index[0]
            if table_name not in index_status:
                index_status[table_name] = {
                    "unique_indices": [],
                    "foreign_keys": [],
                    "normal_indices": []
                }
            
            index_name = index[1]
            is_unique = not bool(index[3])
            
            if is_unique:
                index_status[table_name]["unique_indices"].append(index_name)
            elif index_name.startswith("fk_"):
                index_status[table_name]["foreign_keys"].append(index_name)
            else:
                index_status[table_name]["normal_indices"].append(index_name)
        
        connection.close()
        return index_status

    except Exception as e:
        logger.error(f"检查数据库索引失败: {str(e)}")
        return None 