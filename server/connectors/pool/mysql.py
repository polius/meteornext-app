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
            "use_unicode": True,
            "cursorclass": OrderedDictCursor,
            "autocommit": False,
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

    def execute(self, query, args=None, database=None, conn=None):
        try:
            connection = None
            connection = self._pool.connection() if conn is None else conn
            connection.ping(reconnect=True)
            if database:
                connection.select_db(database)
            with connection.cursor(OrderedDictCursor) as cursor:
                cursor.execute(query, args)
                result = cursor.fetchall() if not query.lstrip().startswith('INSERT INTO') else cursor.lastrowid
            if conn is None:
                connection.commit()
            return result
        finally:
            if conn is None and connection:
                connection.close()

    def mogrify(self, query, args=None):
        try:
            connection = self._pool.connection()
            with connection.cursor(OrderedDictCursor) as cursor:
                return cursor.mogrify(query, args)
        finally:
            connection.close()

    def transaction(self):
        connection = self._pool.connection()
        connection.ping(reconnect=True)
        with connection.cursor(OrderedDictCursor) as cursor:
            cursor.execute("BEGIN")
        return connection

    def commit(self, conn):
        try:
            conn.commit()
        finally:
            conn.close()

    def rollback(self, conn):
        try:
            conn.rollback()
        finally:
            conn.close()
