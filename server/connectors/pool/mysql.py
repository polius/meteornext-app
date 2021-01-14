import pymysql
from collections import OrderedDict
from pymysql.cursors import DictCursorMixin, Cursor
from dbutils.pooled_db import PooledDB

class OrderedDictCursor(DictCursorMixin, Cursor):
    dict_type = OrderedDict

class MySQL:
    def __init__(self, config):
        SQL_CONFIG = {
            "host": config['sql']['hostname'],
            "port": config['sql']['port'],
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
            "maxcached": None,
            "maxshared": None,
            "blocking": True,
            "maxusage": None,
            "setsession": [],
            "ping": 1,
        }
        self._pool = PooledDB(**POOL_CONFIG, **SQL_CONFIG)

    def execute(self, query, args=None, database=None):
        try:
            connection = self._pool.connection()
            connection.ping(reconnect=True)
            if database:
                connection.select_db(database)
            with connection.cursor(OrderedDictCursor) as cursor:
                cursor.execute(query, args)
                return cursor.fetchall() if not query.lstrip().startswith('INSERT INTO') else cursor.lastrowid
        finally:
            connection.close()

    def mogrify(self, query, args=None):
        try:
            connection = self._pool.connection()
            with connection.cursor(OrderedDictCursor) as cursor:
                return cursor.mogrify(query, args)
        finally:
            connection.close()
