import time
import pymysql
import sqlparse
import tempfile
import paramiko
import sshtunnel
import threading
from ssl import CERT_REQUIRED
from pymysql.cursors import DictCursor

class MySQL:
    def __init__(self, server):
        self._server = server
        self._tunnel = None
        self._sql = None
        self._last_execution_time = None
        self._lastrowid = None

    @property
    def last_execution_time(self):
        return self._last_execution_time

    def start(self):
        # Close existing connections
        self.stop()

        # Start new connection
        error = None
        for _ in range(2):
            # Check if thread is alive
            if getattr(threading.current_thread(), 'alive', False) and not threading.current_thread().alive:
                self.stop()
                return

            try:
                # Get SSL
                ssl = self.__get_ssl()
                # Start SSH Tunnel
                if 'ssh' in self._server and self._server['ssh']['enabled']:
                    sshtunnel.SSH_TIMEOUT = 5.0
                    logger = sshtunnel.create_logger(loglevel='CRITICAL')
                    pkey = paramiko.RSAKey.from_private_key_file(self._server['ssh']['key'], password=self._server['ssh']['password'])
                    self._tunnel = sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_password=self._server['ssh']['password'], ssh_pkey=pkey, remote_bind_address=(self._server['sql']['hostname'], self._server['sql']['port']), logger=logger)
                    self._tunnel.start()
                    try:
                        port = self._tunnel.local_bind_port
                    except Exception:
                        raise Exception("Can't connect to the SSH Server.")

                # Start SQL Connection
                hostname = '127.0.0.1' if 'ssh' in self._server and self._server['ssh']['enabled'] else self._server['sql']['hostname']
                port = port if 'ssh' in self._server and self._server['ssh']['enabled'] else self._server['sql']['port']
                database = self._server['sql']['database'] if 'database' in self._server['sql'] else None
                timeout = None if 'timeout' not in self._server['sql'] else self._server['sql']['timeout']
                self._sql = pymysql.connect(host=hostname, port=int(port), user=self._server['sql']['username'], passwd=self._server['sql']['password'], database=database, charset='utf8mb4', use_unicode=True, autocommit=True, read_timeout=timeout, write_timeout=timeout, ssl=ssl)
                return

            except Exception as e:
                # Close Connections
                self.stop()
                error = e
                time.sleep(1)

            finally:
                # Close SSL
                self.__close_ssl(ssl)

        # Raise error
        raise error

    def stop(self):
        self.rollback()
        try:
            self._sql.close()
        except Exception:
            pass

        try:
            self._tunnel.stop(force=True)
        except Exception:
            pass

    def execute(self, query, args=None, database=None):
        try:
            start_time = time.time()
            return self.__execute_query(query, args, database)
        except Exception:
            self.start()
            start_time = time.time()
            return self.__execute_query(query, args, database)
        finally:
            self._last_execution_time = "{0:.3f}".format(time.time() - start_time)

    def mogrify(self, query, args=None):
        with self._sql.cursor(DictCursor) as cursor:
            return cursor.mogrify(query, args)

    def begin(self):
        self._sql.begin()

    def commit(self):
        self._sql.commit()

    def rollback(self):
        try:
            self._sql.rollback()
        except Exception:
            pass

    def lastrowid(self):
        return self._lastrowid

    def __execute_query(self, query, args=None, database=None):
        # Select the database
        if database:
            self._sql.select_db(database)

        # Prepare the cursor
        with self._sql.cursor(DictCursor) as cursor:
            # Execute the SQL query
            cursor.execute(query, args)

            # Get the query results
            query_parsed = sqlparse.format(query, strip_comments=True).strip()[:6].lower()
            query_result = cursor.rowcount if query_parsed.startswith(('insert','update','delete')) else cursor.fetchall()

            # Retrieve last row id
            self._lastrowid = cursor.lastrowid

        # Return query info
        query_data = {"query_result": query_result, "query_rows_affected": cursor.rowcount}
        return query_data

    def __get_ssl(self):
        if 'ssl' not in self._server['sql'] or not self._server['sql']['ssl']:
            return None
        ssl = {}
        # Generate CA Certificate
        if self._server['sql']['ssl_ca_certificate']:
            ssl['ssl_ca_file'] = tempfile.NamedTemporaryFile()
            ssl['ssl_ca_file'].write(self._server['sql']['ssl_ca_certificate'].encode())
            ssl['ssl_ca_file'].flush()
            ssl['ca'] = ssl['ssl_ca_file'].name
        # Generate Client Certificate
        if self._server['sql']['ssl_client_certificate']:
            ssl['ssl_cert_file'] = tempfile.NamedTemporaryFile()
            ssl['ssl_cert_file'].write(self._server['sql']['ssl_client_certificate'].encode())
            ssl['ssl_cert_file'].flush()
            ssl['cert'] = ssl['ssl_cert_file'].name
        # Generate Client Key
        if self._server['sql']['ssl_client_key']:
            ssl['ssl_key_file'] = tempfile.NamedTemporaryFile()
            ssl['ssl_key_file'].write(self._server['sql']['ssl_client_key'].encode())
            ssl['ssl_key_file'].flush()
            ssl['key'] = ssl['ssl_key_file'].name
        # Add optional parameters
        ssl['cipher'] = 'DEFAULT:!EDH:!DHE'
        ssl['check_hostname'] = True
        ssl['verify_mode'] = CERT_REQUIRED
        # Return SSL Data
        return ssl

    def __close_ssl(self, ssl):
        if ssl is None:
            return
        if 'ssl_ca_file' in ssl:
            ssl['ssl_ca_file'].close()
        if 'ssl_cert_file' in ssl:
            ssl['ssl_cert_file'].close()
        if 'ssl_key_file' in ssl:
            ssl['ssl_key_file'].close()

    ####################
    # INTERNAL QUERIES #
    ####################
    def get_all_databases(self):
        query = "SHOW DATABASES"
        result = self.execute(query)['query_result']

        databases = []
        for db in result:
            databases.append(db['Database'])
        return databases

    def check_db_exists(self, db):
        query = "SELECT COUNT(*) AS count FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = \"" + db.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_table_exists(self, db, table):
        query = "SELECT COUNT(*) AS count FROM information_schema.tables WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_column_exists(self, db, table, column):
        query = "SELECT COUNT(*) AS count FROM information_schema.columns WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND column_name = \"" + column.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_index_exists(self, db, table, index):
        query = "SELECT COUNT(*) AS count FROM information_schema.statistics WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND index_name = \"" + index.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) > 0 else False

    def check_pk_exists(self, db, table):
        query = "SELECT COUNT(*) AS count FROM information_schema.statistics WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND index_name = \"PRIMARY\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) >= 1 else False

    def check_pk_exists_columns(self, db, table, columns):
        query = """
            SELECT EXISTS
	        (
                SELECT *
                FROM information_schema.statistics 
                WHERE table_schema = '{}'
                AND table_name = '{}'
                AND column_name IN ({})
                AND index_name = 'PRIMARY'
                GROUP BY table_schema, table_name
                HAVING COUNT(*) = {}
            ) AS exist;
            """.format(db, table, str(columns)[1:-1], len(columns))
        result = self.execute(query)['query_result']
        return True if int(result[0]['exist']) == 1 else False

    def check_fk_exists(self, db, table, column):
        query = "SELECT COUNT(*) AS count FROM information_schema.key_column_usage WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND column_name = \"" + column.strip() + "\" AND referenced_table_name IS NOT NULL"
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_fk_exists_by_name(self, db, table, foreign):
        query = "SELECT COUNT(*) AS count FROM information_schema.key_column_usage WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND constraint_name = \"" + foreign.strip() + "\" AND referenced_table_name IS NOT NULL"
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_partition_exists(self, db, table, partition):
        query = "SELECT COUNT(*) AS count FROM information_schema.partitions WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND partition_name = \"" + partition.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_trigger_exists(self, db, table, trigger):
        query = "SELECT COUNT(*) AS count FROM information_schema.triggers WHERE event_object_schema = \"" + db.strip() + "\" AND event_object_table LIKE \"" + table.strip() + "\" AND trigger_name = \"" + trigger.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_view_exists(self, db, view):
        query = "SELECT COUNT(*) AS count FROM information_schema.views WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + view.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_function_exists(self, db, function):
        query = "SELECT COUNT(*) AS count FROM information_schema.routines WHERE routine_schema = \"" + db.strip() + "\" AND routine_name = \"" + function.strip() + "\" AND routine_type = \"FUNCTION\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_procedure_exists(self, db, procedure):
        query = "SELECT COUNT(*) AS count FROM information_schema.routines WHERE routine_schema = \"" + db.strip() + "\" AND routine_name = \"" + procedure.strip() + "\" AND routine_type = \"PROCEDURE\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_event_exists(self, event):
        query = "SELECT COUNT(*) AS count FROM information_schema.events WHERE EVENT_NAME = \"" + event.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_user_exists(self, user, host):
        query = "SELECT COUNT(*) AS count FROM mysql.user WHERE User = \"" + user + "\" AND Host = \"" + host.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False
