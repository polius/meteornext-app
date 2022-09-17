import tempfile
import pymysql
import paramiko
import sshtunnel
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
            # Get SSL
            ssl = self.__get_ssl()
            # Start SSH Tunnel
            if 'ssh' in self._server and self._server['ssh']['enabled']:
                sshtunnel.SSH_TIMEOUT = 5.0
                sshtunnel.DEFAULT_LOGLEVEL = 50
                logging.getLogger('paramiko.transport').setLevel(logging.CRITICAL+1)
                password = None if self._server['ssh']['password'] is None or len(self._server['ssh']['password'].strip()) == 0 else self._server['ssh']['password']
                pkey = None if self._server['ssh']['key'] is None or len(self._server['ssh']['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._server['ssh']['key']), password=password)
                self._tunnel = sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_password=self._server['ssh']['password'], ssh_pkey=pkey, remote_bind_address=(self._server['sql']['hostname'], int(self._server['sql']['port'])), mute_exceptions=True)
                self._tunnel.start()
                try:
                    port = self._tunnel.local_bind_port
                except Exception:
                    raise Exception("Can't connect to the SSH Server.")

            # Start SQL Connection
            hostname = '127.0.0.1' if 'ssh' in self._server and self._server['ssh']['enabled'] else self._server['sql']['hostname']
            port = port if 'ssh' in self._server and self._server['ssh']['enabled'] else self._server['sql']['port']
            database = self._server['sql']['database'] if 'database' in self._server['sql'] else None
            self._sql = pymysql.connect(host=hostname, port=int(port), user=self._server['sql']['username'], passwd=self._server['sql']['password'], database=database, charset='utf8mb4', use_unicode=True, autocommit=True, ssl=ssl)
        except Exception:
            # Close Connections
            self.stop()
            raise
        finally:
            # Close SSL
            self.__close_ssl(ssl)

    def stop(self):
        try:
            self._sql.close()
        except Exception:
            pass        
        try:
            self._tunnel.stop(force=True)
        except Exception as e:
            pass

    def use(self, database):
        self._sql.select_db(database)

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
            query_result = cursor.fetchall() if cursor.lastrowid is None else cursor.lastrowid

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

    def kill(self, connection_id):
        try:
            self._sql.kill(connection_id)
        except Exception:
            pass

    def test_ssh(self):
        password = None if self._server['ssh']['password'] is None or len(self._server['ssh']['password'].strip()) == 0 else self._server['ssh']['password']
        pkey = None if self._server['ssh']['key'] is None or len(self._server['ssh']['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._server['ssh']['key']), password=password)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())        
        client.connect(hostname=self._server['ssh']['hostname'], port=int(self._server['ssh']['port']), username=self._server['ssh']['username'], password=self._server['ssh']['password'], pkey=pkey, timeout=5)
        client.close()

    def test_sql(self):
        try:
            ssl = self.__get_ssl()
            database = self._server['sql']['database'] if 'database' in self._server['sql'] else None
            # Start SSH Connection
            if self._server['ssh']['enabled']:
                password = None if self._server['ssh']['password'] is None or len(self._server['ssh']['password'].strip()) == 0 else self._server['ssh']['password']
                pkey = None if self._server['ssh']['key'] is None or len(self._server['ssh']['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._server['ssh']['key']), password=password)
                sshtunnel.SSH_TIMEOUT = 5.0
                sshtunnel.DEFAULT_LOGLEVEL = 50
                logging.getLogger('paramiko.transport').setLevel(logging.CRITICAL+1)
                tunnel = sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_password=self._server['ssh']['password'], ssh_pkey=pkey, remote_bind_address=(self._server['sql']['hostname'], int(self._server['sql']['port'])), mute_exceptions=True)
                tunnel.start()
                try:
                    port = tunnel.local_bind_port
                except Exception:
                    raise Exception("Can't connect to the SSH Server.")

            # Start SQL Connection
            host = '127.0.0.1' if self._server['ssh']['enabled'] else self._server['sql']['hostname']
            port = port if self._server['ssh']['enabled'] else self._server['sql']['port']
            conn = pymysql.connect(host=host, port=int(port), user=self._server['sql']['username'], passwd=self._server['sql']['password'], database=database, ssl=ssl)
        finally:
            # Close SSL
            self.__close_ssl(ssl)
            # Close Connections
            try:
                conn.close()
            except Exception:
                pass
            try:
                tunnel.close()
            except Exception:
                pass

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
        ssl['check_hostname'] = self._server['sql']['ssl_verify_ca'] == 1
        ssl['verify_mode'] = ssl['check_hostname'] is True
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
    # INTERNAL METHODS #
    ####################
    def get_variables(self):
        return self.execute('SHOW GLOBAL VARIABLES')

    def get_status(self):
        return self.execute('SHOW GLOBAL STATUS')

    def get_processlist(self):
        return self.execute('SELECT * FROM information_schema.processlist')

    def get_databases(self):
        return self.execute("SELECT schema_name AS 'name' FROM information_schema.schemata ORDER BY name")

    def get_database_size(self, database):
        query = """
            SELECT SUM(data_length) AS 'size'
            FROM information_schema.tables
            WHERE table_schema = %s
        """
        size = self.execute(query, args=(database))[0]['size']
        return 0 if size is None else int(size)

    def get_tables_detailed(self, database):
        query = """
            SELECT table_name AS 'name', table_rows AS 'rows', data_length, index_length, (data_length + index_length) AS 'total_length', engine, row_format, avg_row_length, data_free, auto_increment, c.character_set_name AS 'charset', table_collation AS 'collation', table_comment AS 'comment', create_time AS 'created', update_time AS 'modified'
            FROM information_schema.tables t
            JOIN information_schema.collations c ON c.collation_name = t.table_collation
            WHERE t.table_schema = %s
            ORDER BY table_name
        """
        return self.execute(query, args=(database))
