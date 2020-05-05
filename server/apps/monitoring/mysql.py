import os
import sys
import time
import pymysql
import paramiko
import warnings
import sshtunnel
from io import StringIO
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
        sys_stdout = sys.stdout
        sys.stderr = open(os.devnull, 'w')
        sys.stdeout = open(os.devnull, 'w')

        error = None
        for i in range(1):
            try:
                # Start SSH Tunnel
                if self._server['ssh']['enabled']:
                    sshtunnel.SSH_TIMEOUT = 10.0
                    sshtunnel.TUNNEL_TIMEOUT = 10.0
                    pkey = paramiko.RSAKey.from_private_key(StringIO(self._server['ssh']['key']))
                    self._tunnel = sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_pkey=pkey, remote_bind_address=(self._server['sql']['hostname'], self._server['sql']['port']))
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
                sys.stdout = sys_stdout

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
        try:
            query = """
                SELECT processlist_id AS 'ID', processlist_user AS 'USER', processlist_host AS 'HOST', processlist_db AS 'DB', processlist_command AS 'COMMAND', processlist_time AS 'TIME', processlist_state AS 'STATE', processlist_info AS 'INFO'
                FROM performance_schema.threads 
                WHERE type = 'FOREGROUND'
            """
            result = self.execute(query)
        except Exception:
            return self.__get_processlist_v2()
        else:
            if len(result) == 0:
                return self.__get_processlist_v2()
            return result

    def __get_processlist_v2(self):
        query = "SELECT * FROM information_schema.processlist"
        result = self.execute(query)
        return result
