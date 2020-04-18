import os
import sys
import time
import pymysql
import paramiko
import warnings
import sshtunnel
from collections import OrderedDict
from pymysql.cursors import DictCursorMixin, Cursor

class OrderedDictCursor(DictCursorMixin, Cursor):
    dict_type = OrderedDict

class mysql:
    def __init__(self, server):
        self._server = server
        self._tunnel = None
        self._sql = None

    def start(self):
        # Close existing connections
        self.stop()

        # Supress Errors Output
        sys_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')

        error = None
        for i in range(3):
            try:
                # Start SSH Tunnel
                if self._server['ssh']['enabled']:
                    sshtunnel.SSH_TIMEOUT = 10.0
                    sshtunnel.TUNNEL_TIMEOUT = 10.0
                    self._tunnel = sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_pkey=paramiko.RSAKey.from_private_key_file(self._server['ssh']['key']), remote_bind_address=(self._server['sql']['hostname'], self._server['sql']['port']))
                    self._tunnel.start()

                # Start SQL Connection
                hostname = '127.0.0.1' if self._server['ssh']['enabled'] else self._server['sql']['hostname']
                port = self._tunnel.local_bind_port if self._server['ssh']['enabled'] else self._server['sql']['port']
                database = self._server['sql']['database'] if 'database' in self._server['sql'] else None
                self._sql = pymysql.connect(host=hostname, port=port, user=self._server['sql']['username'], passwd=self._server['sql']['password'], database=database, charset='utf8mb4', use_unicode=True, autocommit=False)
                return

            except Exception as e:
                self.stop()
                error = e
                time.sleep(1)

            finally:
                # Show Errors Output Again
                sys.stderr = sys_stderr

        # Check errors
        if error is not None:
            self.stop()
            raise error

    def stop(self):
        try:
            self._sql.close()
        except Exception:
            pass

        try:
            self._tunnel.stop()
        except Exception:
            pass

    def execute(self, query, args=None, database=None):
        try:
            # Execute the query and return results
            return self.__execute_query(query, args, database)

        except (pymysql.ProgrammingError, pymysql.IntegrityError, pymysql.InternalError) as error:
            raise Exception(error.args[1])

        except Exception as e:
            # Reconnect SSH + SQL
            self.start()

            # Retry the query
            return self.__execute_query(query, args, database)

        except KeyboardInterrupt:
            self.rollback()
            self.close()
            raise KeyboardInterrupt("Program Interrupted by User. Rollback successfully performed.")

    def __execute_query(self, query, args, database):
        # Select the database
        if database:
            self._sql.select_db(database)

        # Prepare the cursor
        with self._sql.cursor(OrderedDictCursor) as cursor:            
            # Execute the SQL query ignoring warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cursor.execute(query, args)

            # Get the query results
            query_result = cursor.fetchall()

        # Return query result
        return query_result

    def begin(self):
        self._sql.begin()

    def commit(self):
        self._sql.commit()

    def rollback(self):
        try:
            self._sql.rollback()
        except Exception:
            pass

    def get_parameters(self):
        query = "SHOW GLOBAL VARIABLES"
        result = self.execute(query)
        return result

    def get_status(self):
        query = "SHOW GLOBAL STATUS"
        result = self.execute(query)
        return result

    def get_processlist(self):
        query = "SELECT * FROM information_schema.processlist"
        result = self.execute(query)
        return result

    def get_processlist_v2(self):
        query = """
            SELECT processlist_id AS 'id', processlist_user AS 'user', processlist_host AS 'host', processlist_db AS 'db', processlist_command AS 'command', processlist_time AS 'time', processlist_state AS 'state', processlist_info AS 'info'
            FROM performance_schema.threads 
            WHERE type = 'FOREGROUND'
        """
        result = self.execute(query)
        return result