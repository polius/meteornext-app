import os
import pymysql
import paramiko
import sshtunnel
import threading
import logging
from io import StringIO
from collections import OrderedDict
from pymysql.cursors import DictCursorMixin, Cursor

class OrderedDictCursor(DictCursorMixin, Cursor):
    dict_type = OrderedDict

class MySQL:
    def __init__(self, server):
        self._server = server
        self._tunnel = None
        self._sql = None

    def connect(self):
        # Close existing connections
        self.stop()

        try:
            # Start SSH Tunnel
            if 'ssh' in self._server and self._server['ssh']['enabled']:
                pkey = None if self._server['ssh']['key'] is None or len(self._server['ssh']['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._server['ssh']['key']), password=self._server['ssh']['password'])
                self._tunnel = sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_password=self._server['ssh']['password'], ssh_pkey=pkey, remote_bind_address=(self._server['sql']['hostname'], self._server['sql']['port']), mute_exceptions=True, logger=self.__logger())
                self._tunnel.start()

            # Start SQL Connection
            hostname = '127.0.0.1' if 'ssh' in self._server and self._server['ssh']['enabled'] else self._server['sql']['hostname']
            port = self._tunnel.local_bind_port if 'ssh' in self._server and self._server['ssh']['enabled'] else self._server['sql']['port']
            database = self._server['sql']['database'] if 'database' in self._server['sql'] else None
            self._sql = pymysql.connect(host=hostname, port=port, user=self._server['sql']['username'], passwd=self._server['sql']['password'], database=database, charset='utf8mb4', use_unicode=True, autocommit=True)

        except Exception as e:
            self.stop()
            raise

    def stop(self):
        try:
            self._sql.close()
        except Exception:
            pass        
        try:
            self._tunnel.stop(force=True)
        except Exception:
            pass

    def execute(self, query, args=None, database=None, retry=True):
        try:
            return self.__execute_query(query, args, database)
        except Exception as e:
            if retry:
                self.connect()
                return self.execute(query, args, database, retry=False)
            raise

    def __execute_query(self, query, args, database):
        # Select the database
        if database:
            self._sql.select_db(database)

        # Prepare the cursor
        with self._sql.cursor(OrderedDictCursor) as cursor:
            # Execute the SQL query
            cursor.execute(query, args)

            # Get the query results
            query_result = cursor.fetchall() if not query.lstrip().startswith('INSERT INTO') else cursor.lastrowid

        # Return query info
        return query_result

    def mogrify(self, query, args=None, retry=True):
        try:
            with self._sql.cursor(OrderedDictCursor) as cursor:
                return cursor.mogrify(query, args)
        except Exception as e:
            if retry:
                self.connect()
                return self.mogrify(query, args, retry=False)
            raise

    def test_ssh(self):
        pkey = None if self._server['ssh']['key'] is None or len(self._server['ssh']['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._server['ssh']['key']), password=self._server['ssh']['password'])
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        with client.connect(hostname=self._server['ssh']['hostname'], port=int(self._server['ssh']['port']), username=self._server['ssh']['username'], password=self._server['ssh']['password'], pkey=pkey, timeout=10):
            pass

    def test_sql(self):
        if self._server['ssh']['enabled']:
            pkey = None if self._server['ssh']['key'] is None or len(self._server['ssh']['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._server['ssh']['key']), password=self._server['ssh']['password'])
            sshtunnel.SSH_TIMEOUT = 10.0
            with sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_password=self._server['ssh']['password'], ssh_pkey=pkey, remote_bind_address=(self._server['sql']['hostname'], int(self._server['sql']['port'])), threaded=False) as tunnel:
                conn = pymysql.connect(host='127.0.0.1', port=tunnel.local_bind_port, user=self._server['sql']['username'], passwd=self._server['sql']['password'])
                conn.close()
        else:
            conn = pymysql.connect(host=self._server['sql']['hostname'], port=int(self._server['sql']['port']), user=self._server['sql']['username'], passwd=self._server['sql']['password'])
            conn.close()

    def __logger(self):
        # Create a Logger to suppress sshtunnel warnings
        log = logging.getLogger('sshtunnel')
        log.setLevel(level=logging.CRITICAL)
        if not log.hasHandlers():
            sh = logging.StreamHandler()
            sh.setLevel(level=logging.CRITICAL)
            log.addHandler(sh)
        return log

    ####################
    # INTERNAL METHODS #
    ####################
    def check_db_exists(self, db):
        result = self.execute('SELECT COUNT(*) AS count FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s', args=(db.strip()))
        return True if int(result[0]['count']) == 1 else False

    def get_variables(self):
        return self.execute('SHOW GLOBAL VARIABLES')

    def get_status(self):
        return self.execute('SHOW GLOBAL STATUS')

    def get_processlist(self):
        return self.execute('SELECT * FROM information_schema.processlist')
