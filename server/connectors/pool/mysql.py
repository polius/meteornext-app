import pymysql
import time
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
            "ssl_ca":  'keys/' + config['ssl_ca_certificate'] if 'ssl_ca_certificate' in config and config['ssl_ca_certificate'] else None,
            "ssl_cert": 'keys/' + config['ssl_client_certificate'] if 'ssl_client_certificate' in config and config['ssl_client_certificate'] else None,
            "ssl_key": 'keys/' + config['ssl_client_key'] if 'ssl_client_key' in config and config['ssl_client_key'] else None,
            "ssl_verify_cert": config.get('ssl_verify_ca') == 1,
            "ssl_verify_identity": config.get('ssl_verify_ca') == 1
        }
        POOL_CONFIG = {
            "creator": pymysql,
            "maxconnections": None,
            "mincached": 0,
            "maxcached": 20,
            "maxshared": 0,
            "blocking": True,
            "maxusage": 0,
            "setsession": [],
            "ping": 1,
        }
        self._pool = dbutils.pooled_db.PooledDB(**POOL_CONFIG, **SQL_CONFIG)

    def execute(self, query, args=None, database=None):
        retries = 2
        exception = None
        for _ in range(retries+1):
            try:
                with self._pool.dedicated_connection() as connection:
                    if database:
                        connection.select_db(database)
                    with connection.cursor(OrderedDictCursor) as cursor:
                        cursor.execute(query, args)
                        result = cursor.fetchall() if cursor.lastrowid is None else cursor.lastrowid
                    connection.commit()
                return result
            except Exception as e:
                exception = e
                time.sleep(1)
        raise exception

    def mogrify(self, query, args=None):
        with self._pool.dedicated_connection() as connection:
            with connection.cursor(OrderedDictCursor) as cursor:
                result = cursor.mogrify(query, args)
        return result

    def raw(self, transaction=True):
        connection = self._pool.dedicated_connection()
        if transaction:
            connection.begin()
        cursor = connection.cursor(OrderedDictCursor)
        return [connection, cursor]
