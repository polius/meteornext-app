import uuid
import time
import tempfile
import pymysql
import paramiko
import threading
import sshtunnel
import traceback
import logging
from io import StringIO
from ssl import CERT_REQUIRED
from pymysql.cursors import DictCursor
from pymysql.constants import CLIENT

import connectors.base

class MySQL:
    def __init__(self, server):
        # Server Credentials
        self._server = server
        # Objects
        self._tunnel = None
        self._sql = None
        self._cursor = None
        # Internal variables
        self._connection_id = None
        self._query_uuid = None
        self._start_execution = None
        self._last_execution = None
        self._is_executing = False
        self._is_protected = False
        self._is_transaction = False
        self._locks = []

    @property
    def start_execution(self):
        return self._start_execution

    @property
    def last_execution(self):
        return self._last_execution

    @property
    def is_executing(self):
        return self._is_executing

    @property
    def is_protected(self):
        return self._is_protected

    @is_protected.setter
    def is_protected(self, value):
        self._is_protected = value

    @property
    def is_transaction(self):
        return self._is_transaction

    @property
    def connection_id(self):
        return self._connection_id

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, value):
        self._server = value

    def connect(self):
        retries = 2
        exception = None
        for _ in range(retries):
            # Close existing connections
            self.close()

            try:
                ssl = self.__get_ssl()
                # Start SSH Tunnel
                if self._server['ssh']['enabled']:
                    sshtunnel.SSH_TIMEOUT = 5.0
                    sshtunnel.DEFAULT_LOGLEVEL = 50
                    logging.getLogger('paramiko.transport').setLevel(logging.CRITICAL+1)
                    pkey = None if self._server['ssh']['key'] is None or len(self._server['ssh']['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._server['ssh']['key']), password=self._server['ssh']['password'])
                    self._tunnel = sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_password=self._server['ssh']['password'], ssh_pkey=pkey, remote_bind_address=(self._server['sql']['hostname'], int(self._server['sql']['port'])), mute_exceptions=True)
                    self._tunnel.start()
                    try:
                        port = self._tunnel.local_bind_port
                    except Exception:
                        raise Exception("Can't connect to the SSH Server.")

                # Start SQL Connection
                hostname = '127.0.0.1' if self._server['ssh']['enabled'] else self._server['sql']['hostname']
                port = port if self._server['ssh']['enabled'] else self._server['sql']['port']
                database = self._server['sql']['database'] if 'database' in self._server['sql'] else None
                self._sql = pymysql.connect(host=hostname, port=int(port), user=self._server['sql']['username'], passwd=self._server['sql']['password'], database=database, charset='utf8mb4', use_unicode=True, autocommit=True, client_flag=CLIENT.MULTI_STATEMENTS, ssl=ssl)
                self._connection_id = self._sql.thread_id()
                return

            except Exception as e:
                # Close Connections
                self.close()
                exception = e
                time.sleep(1)
            finally:
                self.__close_ssl(ssl)

        # Raise Exception
        raise exception

    def close(self):
        try:
            self._cursor.close()
        except Exception:
            pass

        try:
            self._sql.close()
        except Exception:
            pass

        try:
            self._tunnel.stop(force=True)
        except Exception:
            pass

    def execute(self, query, args=None, database=None, fetch=True, import_file=False, skip_lock=False):
        self._is_executing = True
        self._query_uuid = str(uuid.uuid4())
        if not skip_lock:
            self._locks.append(self._query_uuid)
            while self._locks[0] != self._query_uuid:
                time.sleep(1)

        # Check connection
        self.__check_connection()

        # Check transaction
        if not import_file:
            if query.strip()[:17].upper().startswith('START TRANSACTION') or query.strip()[:5].upper().startswith('BEGIN'):
                self._is_transaction = True
            elif query.strip()[:6].upper().startswith('COMMIT') or query.strip()[:8].upper().startswith('ROLLBACK'):
                self._is_transaction = False

        # Execute query
        try:
            return self.__execute_query(query, args, database, fetch)
        except Exception as e:
            # Handle MySQL error "Table definition has changed, please retry transaction" when cloning an object.
            if e.__class__.__name__ == 'OperationalError' and e.args[0] == 1412:
                self.connect()
                return self.__execute_query(query, args, database, fetch)
            raise
        finally:
            self._last_execution = time.time()
            self._is_executing = False
            self._is_protected = False
            if not skip_lock:
                del self._locks[0]

    def __execute_query(self, query, args, database, fetch):
        self._start_execution = time.time()
        # Select the database
        if database:
            self._sql.select_db(database)

        # Start timeout manager
        t = None
        timeout_type = self._server['sql']['timeout_type'] if 'timeout_type' in self._server['sql'] else None
        timeout_value = self._server['sql']['timeout_value'] if 'timeout_value' in self._server['sql'] else None
        execution_rows = self._server['sql']['execution_rows'] if 'execution_rows' in self._server['sql'] else None
        if timeout_type is not None and timeout_value is not None:
            t = threading.Thread(target=self.__timeout_query, args=(query, self._query_uuid, timeout_type, timeout_value,))
            t.start()

        # Prepare the cursor
        if fetch:
            with self._sql.cursor(DictCursor) as cursor:
                # Execute the SQL query
                cursor.execute(query, args)

                # Get the query results
                data = cursor.fetchmany(execution_rows) if execution_rows else cursor.fetchall()
        else:
            self._cursor = self._sql.cursor(DictCursor)
            self._cursor.execute(query, args)

        # Return query info
        if fetch:
            rowcount = cursor.rowcount if query.lower().startswith(('insert','update','delete')) else len(data)
            query_data = {"data": data, "lastRowId": cursor.lastrowid, "rowCount": rowcount}
            return query_data

    def __check_connection(self):
        try:
            with self._sql.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            self.connect()

    def __timeout_query(self, query, query_id, timeout_type, timeout_value):
        is_select = query[:6].lower() == 'select'
        condition = timeout_type == 'all' or (timeout_type == 'select' and is_select)
        i = 0
        while condition and self._query_uuid == query_id:
            if i >= timeout_value:
                try:
                    sql = connectors.base.Base(self._server)
                    sql.connect()
                    sql.kill(self._connection_id)
                    sql.stop()
                except Exception:
                    traceback.print_exc()
                finally:
                    break
            time.sleep(1)
            i += 1

    def stop_timeout(self):
        self._query_uuid = None

    def fetch_one(self):
        if self._cursor:
            return self._cursor.fetchone()

    def fetch_many(self, size):
        if self._cursor:
            return self._cursor.fetchmany(size=size)

    def begin(self):
        self._sql.begin()

    def commit(self):
        if not self._is_transaction:
            self._sql.commit()

    def rollback(self):
        try:
            self._sql.rollback()
        except Exception:
            pass

    def mogrify(self, query, args):
        with self._sql.cursor(DictCursor) as cursor:    
            return cursor.mogrify(query, args)
    
    def kill(self, connection_id):
        try:
            self._sql.kill(connection_id)
        except Exception:
            pass

    def explain(self, query, database=None):
        return self.execute('EXPLAIN {}'.format(query), database=database)['data']

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
    def get_server_variables(self):
        query = "SHOW GLOBAL VARIABLES"
        result = self.execute(query)['data']
        variables = []
        for v in result:
            variables.append({ 'variable': v['Variable_name'], 'value': v['Value'] })
        return variables

    def get_default_encoding(self):
        query = "SHOW VARIABLES LIKE 'character_set_server'"
        result = self.execute(query)['data'][0]['Value']
        return result

    def get_default_collation(self):
        query = "SHOW VARIABLES LIKE 'collation_server'"
        result = self.execute(query)['data'][0]['Value']
        return result

    def get_version(self):
        query = "SHOW VARIABLES LIKE 'version'"
        result = self.execute(query)['data'][0]['Value']
        return result

    def get_engines(self):
        query = """
            SELECT engine, support 
            FROM information_schema.engines 
            WHERE SUPPORT IN ('DEFAULT', 'YES')
            ORDER BY engine
        """
        result = self.execute(query)['data']
        return result

    def get_encodings(self):
        query = """
            SELECT character_set_name AS 'encoding', default_collate_name AS 'collation', description
            FROM information_schema.character_sets 
            ORDER BY character_set_name
        """
        result = self.execute(query)['data']
        return result

    def get_collations(self, encoding):
        query = """
            SELECT collation_name AS 'collation'
            FROM information_schema.collations 
            WHERE character_set_name = %s
            ORDER BY collation_name ASC
        """
        result = self.execute(query, args=(encoding))['data']
        collations = []
        for c in result:
            collations.append(c['collation'])
        return collations

    def get_all_databases(self):
        query = """
            SELECT schema_name AS 'name'
            FROM information_schema.schemata
            ORDER BY schema_name
        """
        result = self.execute(query)['data']
        databases = []
        for db in result:
            databases.append(db['name'])
        return databases

    def get_all_tables(self, db):
        query = """
            SELECT table_name AS 'name', IF(table_type = 'VIEW', 'view','table') AS 'type'
            FROM information_schema.tables 
            WHERE table_schema = %s
            ORDER BY table_name
        """
        return self.execute(query, args=(db))['data']

    def get_all_columns(self, db):
        query = """
            SELECT DISTINCT column_name AS 'name', column_type AS 'type'
            FROM information_schema.columns
            WHERE table_schema = %s
            ORDER BY 'name'
        """
        return self.execute(query, args=(db))['data']

    def get_all_triggers(self, db):
        query = "SHOW TRIGGERS"
        result = self.execute(query, database=db)['data']
        triggers = []
        for t in result:
            triggers.append(t['Trigger'])
        return triggers

    def get_all_events(self, db):
        query = """
            SELECT event_name AS 'name'
            FROM information_schema.events
            WHERE event_schema = %s
            ORDER BY event_name
        """
        return self.execute(query, args=(db))['data']

    def get_all_routines(self, db):
        query = """
            SELECT routine_name AS 'name', LOWER(routine_type) AS 'type'
            FROM information_schema.routines
            WHERE routine_schema = %s
            ORDER BY routine_name
        """
        return self.execute(query, args=(db))['data']

    def get_columns(self, db, table):
        query = """
            SELECT 
                column_name AS 'Name', 
                UPPER(data_type) AS 'Type', 
                IF(data_type = 'enum', SUBSTRING(column_type, 6, CHAR_LENGTH(column_type)-6), COALESCE(character_maximum_length, numeric_precision)) AS 'Length',
                column_type LIKE '%% unsigned' AS 'Unsigned',
                IF(is_nullable = 'YES', true, false) AS 'Allow NULL',
                column_key AS 'Key',
                extra AS 'Extra',
                column_default AS 'Default',
                character_set_name AS 'Encoding',
                collation_name AS 'Collation',
                column_comment AS 'Comment'
            FROM information_schema.columns 
            WHERE table_schema = %s
            AND table_name = %s
            ORDER BY ordinal_position
        """
        return self.execute(query, args=(db, table))['data']

    def get_indexes(self, db, table):
        query = """
            SELECT 
                index_name AS 'Name',
                CASE 
                WHEN index_type = 'FULLTEXT' THEN 'FULLTEXT'
                    WHEN index_name = 'PRIMARY' THEN 'PRIMARY'
                    WHEN non_unique = 0 THEN 'UNIQUE'
                    ELSE 'INDEX'
                END AS 'Type', 
                GROUP_CONCAT(column_name ORDER BY seq_in_index) AS 'Fields'
            FROM information_schema.statistics
            WHERE table_schema = %s
            AND table_name = %s
            GROUP BY index_name, index_type, non_unique
        """
        return self.execute(query, args=(db, table))['data']

    def get_fks(self, db, table):
        query = """
            SELECT 
                r.constraint_name AS 'Name', 
                k.column_name AS 'Column', 
                k.referenced_table_schema AS 'FK Database', 
                k.referenced_table_name AS 'FK Table', 
                k.referenced_column_name AS 'FK Column', 
                r.update_rule AS 'On Update', 
                r.delete_rule AS 'On Delete'
            FROM
            (
                SELECT constraint_name, constraint_schema, update_rule, delete_rule
                FROM information_schema.REFERENTIAL_CONSTRAINTS
                WHERE constraint_schema = %(db)s
                AND table_name = %(table)s
            ) r
            JOIN
            (
                SELECT constraint_name, column_name, table_schema, referenced_table_schema, referenced_table_name, referenced_column_name
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE table_schema = %(db)s
                AND table_name = %(table)s
            ) k ON k.constraint_name = r.constraint_name AND k.table_schema = r.constraint_schema
        """
        return self.execute(query, args={"db": db, "table": table})['data']
    
    def get_triggers(self, db, table):
        query = """
            SELECT trigger_name AS 'Name', action_timing AS 'Timing', action_statement AS 'Statement', event_manipulation AS 'Event', definer AS 'Definer', created AS 'Created', character_set_client AS 'Character Set Client', collation_connection AS 'Collation Connection', database_collation AS 'Database Collation'
            FROM information_schema.triggers
            WHERE event_object_schema = %s
            AND event_object_table = %s
        """
        return self.execute(query, args=(db, table))['data']

    def get_column_names(self, db, table):
        query = "SELECT COLUMN_NAME, COLUMN_DEFAULT, DATA_TYPE, EXTRA FROM information_schema.columns WHERE table_schema = '" + db.strip() + "' AND table_name = '" + table.strip() + "' ORDER BY ordinal_position"
        result = self.execute(query)['data']

        columns = {'name': [], 'default': [], 'type': {}, 'extra': []}
        for cl in result:
            columns['name'].append(cl['COLUMN_NAME'])
            columns['default'].append(cl['COLUMN_DEFAULT'])
            columns['type'][cl['COLUMN_NAME']] = cl['DATA_TYPE']
            columns['extra'].append(cl['EXTRA'])
        return columns

    def get_pk_names(self, db, table):
        query = "SELECT COLUMN_NAME FROM information_schema.statistics WHERE table_schema = '" + db.strip() + "' AND table_name = '" + table.strip() + "' AND index_name = 'PRIMARY'"
        result = self.execute(query)['data']
        
        columns = []
        for cl in result:
            columns.append(cl['COLUMN_NAME'])
        return columns

    def get_table_info(self, db, table=None):
        table = '' if table is None else "AND t.table_name = '{}'".format(table)
        query = """
            SELECT table_name AS 'name', table_rows AS 'rows', data_length AS 'data_length', index_length AS 'index_length', (data_length + index_length) AS 'total_length', engine, row_format, avg_row_length, data_free, auto_increment, c.character_set_name AS 'charset', table_collation AS 'collation', table_comment AS 'comment', create_time AS 'created', update_time AS 'modified'
            FROM information_schema.tables t
            JOIN information_schema.collations c ON c.collation_name = t.table_collation
            WHERE t.table_schema = '{}'
            {}
            ORDER BY table_name
        """.format(db, table).strip()
        result = self.execute(query)['data']
        return result

    def get_table_syntax(self, db, table):
        query = "SHOW CREATE TABLE `{}`.`{}`".format(db, table)
        result = self.execute(query)['data'][0]['Create Table']
        return result

    def get_view_info(self, db, view):
        view = '' if view is None else "AND table_name = '{}'".format(view)
        query = """
            SELECT table_name AS 'name', check_option, is_updatable, definer, character_set_client AS 'charset', collation_connection AS 'collation'
            FROM information_schema.views
            WHERE table_schema = '{}'
            {}
            ORDER BY table_name
        """.format(db, view).strip()
        result = self.execute(query)['data']
        return result

    def get_view_syntax(self, db, view):
        query = """
            SELECT view_definition 
            FROM information_schema.views 
            WHERE table_schema = %s
            AND table_name = %s
        """
        result = self.execute(query, args=(db, view))['data'][0]['view_definition']
        return f"CREATE VIEW `{view}` AS {result}"

    def get_trigger_info(self, db, trigger=None):
        trigger = '' if trigger is None else "AND trigger_name = '{}'".format(trigger)
        query = """
            SELECT trigger_name AS 'name', event_object_table 'table', action_timing AS 'timing', event_manipulation AS 'event', definer, character_set_client AS 'charset', collation_connection AS 'collation', created
            FROM information_schema.triggers
            WHERE event_object_schema = '{}'
            {}
            ORDER BY trigger_name
        """.format(db, trigger).strip()
        return self.execute(query)['data']

    def get_trigger_syntax(self, db, trigger):
        query = "SHOW CREATE TRIGGER `{}`.`{}`".format(db, trigger)
        result = self.execute(query)['data'][0]['SQL Original Statement']
        return result

    def get_function_info(self, db, function=None):
        function = '' if function is None else "AND routine_name = '{}'".format(function)
        query = """
            SELECT routine_name AS 'name', dtd_identifier AS 'return_type', is_deterministic, definer, character_set_client AS 'charset', collation_connection AS 'collation', created
            FROM information_schema.routines 
            WHERE routine_schema = '{}'
            AND routine_type = 'FUNCTION'
            {}
            ORDER BY routine_name
        """.format(db, function).strip()
        return self.execute(query)['data']

    def get_function_syntax(self, db, function):
        query = "SHOW CREATE FUNCTION `{}`.`{}`".format(db, function)
        result = self.execute(query)['data'][0]['Create Function']
        return result

    def get_procedure_info(self, db, procedure=None):
        procedure = '' if procedure is None else "AND routine_name = '{}'".format(procedure)
        query = """
            SELECT routine_name AS 'name', is_deterministic, definer, character_set_client AS 'charset', collation_connection AS 'collation', created
            FROM information_schema.routines 
            WHERE routine_schema = '{}'
            AND routine_type = 'PROCEDURE'
            {}
            ORDER BY routine_name
        """.format(db, procedure).strip()
        return self.execute(query)['data']

    def get_procedure_syntax(self, db, procedure):
        query = "SHOW CREATE PROCEDURE `{}`.`{}`".format(db, procedure)
        result = self.execute(query)['data'][0]['Create Procedure']
        return result

    def get_event_info(self, db, event=None):
        event = '' if event is None else "AND event_name = '{}'".format(event)
        query = """
            SELECT event_name AS 'name', event_type AS 'type', execute_at, interval_value, interval_field, starts, ends, on_completion, definer, character_set_client AS 'charset', collation_connection AS 'collation', created
            FROM information_schema.events
            WHERE event_schema = '{}'
            {}
            ORDER BY event_name
        """.format(db, event).strip()
        return self.execute(query)['data']

    def get_event_syntax(self, db, event):
        query = "SHOW CREATE EVENT `{}`.`{}`".format(db, event)
        result = self.execute(query)['data'][0]['Create Event']
        return result

    def get_columns_definition(self, db, table):
        query = """
            SELECT column_name, column_type
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = %s
        """
        result = self.execute(query, args=(db, table))['data']
        return result

    def get_all_rights(self):
        # self.execute("FLUSH PRIVILEGES")
        query = "SELECT `user`, `host` FROM mysql.`user` ORDER BY `user`, `host`"
        return self.execute(query)['data']

    def get_server_rights(self, user, host):
        query = """
            SELECT *
            FROM `user`
            WHERE `user` = %s
            AND `host` = %s;
        """
        return self.execute(query, args=(user, host), database='mysql')['data']

    def get_db_rights(self, user, host):
        query = """
            SELECT *
            FROM db
            WHERE `user` = %s
            AND `host` = %s
            ORDER BY db;
        """
        return self.execute(query, args=(user, host), database='mysql')['data']

    def get_table_rights(self, user, host):
        query = """
            SELECT db, table_name, table_priv 
            FROM mysql.tables_priv
            WHERE `user` = %s
            AND `host` = %s
            AND table_priv != ''
            ORDER BY db, table_name;
        """
        return self.execute(query, args=(user, host), database='mysql')['data']

    def get_column_rights(self, user, host):
        query = """
            SELECT db, table_name, column_name, column_priv
            FROM columns_priv
            WHERE `user` = %s
            AND `host` = %s
            ORDER BY db, table_name, column_name;
        """
        return self.execute(query, args=(user, host), database='mysql')['data']

    def get_proc_rights(self, user, host):
        query = """
            SELECT db, routine_name, routine_type, proc_priv
            FROM procs_priv
            WHERE `user` = %s
            AND `host` = %s
            ORDER BY db, routine_name
        """
        return self.execute(query, args=(user, host), database='mysql')['data']

    def get_rights_syntax(self, user, host):
        query = "SHOW GRANTS FOR %s@%s"
        return self.execute(query, args=(user, host), database='mysql')['data']

    def enable_fks_checks(self):
        query = "SET FOREIGN_KEY_CHECKS = 1"
        self.execute(query)

    def disable_fks_checks(self):
        query = "SET FOREIGN_KEY_CHECKS = 0"
        self.execute(query)

    def get_table_pks(self, database, table):
        query = """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_schema = %s
            AND table_name = %s
            AND column_key = 'PRI'
        """
        result = self.execute(query, args=(database, table))['data']
        return [pk['column_name'] for pk in result]

    def get_processlist(self):
        query = "SHOW FULL PROCESSLIST"
        return self.execute(query)['data']
