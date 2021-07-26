import pymysql
import dbutils.pooled_db
from collections import OrderedDict
from pymysql.cursors import DictCursorMixin, Cursor

class OrderedDictCursor(DictCursorMixin, Cursor):
    dict_type = OrderedDict

class MySQL:
    def __init__(self, config):
        SQL_CONFIG = {
            "host": config['hostname'],
            "port": int(config['port']),
            "db": config['database'],
            "password": config['password'],
            "user": config['username'],
            "charset": "utf8mb4",
            "use_unicode": True,
            "cursorclass": OrderedDictCursor,
            "autocommit": False,
            "ssl_ca": config.get('ssl_ca_certificate'),
            "ssl_cert": config.get('ssl_client_certificate'),
            "ssl_key": config.get('ssl_client_key'),
            "ssl_verify_cert": config.get('ssl_verify_ca') == 1,
            "ssl_verify_identity": config.get('ssl_verify_ca') == 1
        }
        POOL_CONFIG = {
            "creator": pymysql,
            "maxconnections": None,
            "mincached": 1,
            "maxcached": 10,
            "maxshared": 0,
            "blocking": True,
            "maxusage": 0,
            "setsession": [],
            "ping": 1,
        }
        self._pool = dbutils.pooled_db.PooledDB(**POOL_CONFIG, **SQL_CONFIG)

    def execute(self, query, args=None, database=None):
        with self._pool.dedicated_connection() as connection:
            if database:
                connection.select_db(database)
            with connection.cursor(OrderedDictCursor) as cursor:
                cursor.execute(query, args)
                result = cursor.fetchall() if cursor.lastrowid is None else cursor.lastrowid
            connection.commit()
        return result

    def mogrify(self, query, args=None):
        with self._pool.dedicated_connection() as connection:
            with connection.cursor(OrderedDictCursor) as cursor:
                result = cursor.mogrify(query, args)
        return result
