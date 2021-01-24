import pymysql
import dbutils.pooled_db
from collections import OrderedDict
from pymysql.cursors import DictCursorMixin, Cursor

class OrderedDictCursor(DictCursorMixin, Cursor):
    dict_type = OrderedDict

class MySQL:
    def __init__(self, config):
        SQL_CONFIG = {
            "host": config['sql']['hostname'],
            "port": int(config['sql']['port']),
            "db": config['sql']['database'],
            "password": config['sql']['password'],
            "user": config['sql']['username'],
            "charset": "utf8mb4",
            "cursorclass": OrderedDictCursor,
            "autocommit": True,
        }
        POOL_CONFIG = {
            "creator": pymysql,
            "maxconnections": None,
            "mincached": 1,
            "maxcached": 10,
            "maxshared": None,
            "blocking": True,
            "maxusage": None,
            "setsession": [],
            "ping": 1,
        }
        self._pool = dbutils.pooled_db.PooledDB(**POOL_CONFIG, **SQL_CONFIG)

    def execute(self, query, args=None, database=None):
        try:
            conn = self._pool.connection()
            conn.ping(reconnect=True)
            if database:
                conn.select_db(database)
            with conn.cursor(OrderedDictCursor) as cursor:
                cursor.execute(query, args)
                return cursor.fetchall() if not query.lstrip().startswith('INSERT INTO') else cursor.lastrowid
        finally:
            conn.close()

    def mogrify(self, query, args=None):
        try:
            conn = self._pool.connection()
            with conn.cursor(OrderedDictCursor) as cursor:
                return cursor.mogrify(query, args)
        finally:
            conn.close()
