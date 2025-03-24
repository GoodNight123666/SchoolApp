
import pymysql
from pymysql.cursors import DictCursor
from config import MYSQL_CONFIG
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        self.last_connection_time = 0
        self.connection_timeout = 300  # 5分钟连接超时时间
        self.max_retries = 3  # 最大重试次数
    
    def connect(self):
        current_time = time.time()
        
        # 检查连接是否已过期或不存在
        if (self.connection is None or 
            current_time - self.last_connection_time > self.connection_timeout):
            
            # 如果有旧连接，尝试关闭
            if self.connection:
                try:
                    self.connection.close()
                except Exception:
                    pass
                self.connection = None
            
            # 创建新连接
            try:
                self.connection = pymysql.connect(
                    host=MYSQL_CONFIG["host"],
                    port=MYSQL_CONFIG["port"],
                    user=MYSQL_CONFIG["user"],
                    password=MYSQL_CONFIG["password"],
                    database=MYSQL_CONFIG["database"],
                    charset=MYSQL_CONFIG["charset"],
                    cursorclass=DictCursor,
                    connect_timeout=10
                )
                self.last_connection_time = current_time
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Database connection error: {str(e)}")
                raise e
                
        # 验证连接是否有效
        try:
            self.connection.ping(reconnect=True)
            self.last_connection_time = current_time
        except Exception as e:
            logger.warning(f"Connection ping failed, reconnecting: {str(e)}")
            self.connection = None
            return self.connect()  # 递归尝试重新连接
            
        return self.connection
    
    def execute_query(self, query, params=None, retries=0):
        try:
            connection = self.connect()
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                result = cursor.fetchall()
                logger.debug(f"Query executed: {query}")
                return result
        except (pymysql.OperationalError, pymysql.InterfaceError) as e:
            # 处理连接断开或超时错误
            connection = None
            self.connection = None
            if retries < self.max_retries:
                logger.warning(f"Database error, retrying ({retries+1}/{self.max_retries}): {str(e)}")
                time.sleep(0.5)  # 短暂延迟后重试
                return self.execute_query(query, params, retries+1)
            else:
                logger.error(f"Query error after {self.max_retries} retries: {str(e)}")
                raise e
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            if connection:
                connection.rollback()
            raise e
    
    def execute_insert(self, query, params=None, retries=0):
        try:
            connection = self.connect()
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                connection.commit()
                logger.debug(f"Insert executed: {query}")
                return cursor.lastrowid
        except (pymysql.OperationalError, pymysql.InterfaceError) as e:
            # 处理连接断开或超时错误
            self.connection = None
            if retries < self.max_retries:
                logger.warning(f"Database error, retrying ({retries+1}/{self.max_retries}): {str(e)}")
                time.sleep(0.5)  # 短暂延迟后重试
                return self.execute_insert(query, params, retries+1)
            else:
                logger.error(f"Insert error after {self.max_retries} retries: {str(e)}")
                raise e
        except Exception as e:
            logger.error(f"Insert error: {str(e)}")
            if self.connection:
                self.connection.rollback()
            raise e
    
    def execute_update(self, query, params=None, retries=0):
        try:
            connection = self.connect()
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                connection.commit()
                logger.debug(f"Update executed: {query}")
                return cursor.rowcount
        except (pymysql.OperationalError, pymysql.InterfaceError) as e:
            # 处理连接断开或超时错误
            self.connection = None
            if retries < self.max_retries:
                logger.warning(f"Database error, retrying ({retries+1}/{self.max_retries}): {str(e)}")
                time.sleep(0.5)  # 短暂延迟后重试
                return self.execute_update(query, params, retries+1)
            else:
                logger.error(f"Update error after {self.max_retries} retries: {str(e)}")
                raise e
        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            if self.connection:
                self.connection.rollback()
            raise e
    
    def close(self):
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
            finally:
                self.connection = None

# 创建共享实例
db = Database()
