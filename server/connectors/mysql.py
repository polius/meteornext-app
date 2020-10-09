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
from pymysql.constants import CLIENT

class OrderedDictCursor(DictCursorMixin, Cursor):
    dict_type = OrderedDict

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
        self._last_execution = None
        self._is_executing = False

    @property
    def last_execution(self):
        return self._last_execution

    @property
    def is_executing(self):
        return self._is_executing

    @property
    def connection_id(self):
        return self._connection_id

    def connect(self):
        # Close existing connections
        self.close()

        # Supress Errors Output
        sys_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')

        error = None
        for i in range(3):
            try:
                # Start SSH Tunnel
                if self._server['ssh']['enabled']:
                    sshtunnel.SSH_TIMEOUT = 5.0
                    sshtunnel.TUNNEL_TIMEOUT = 5.0
                    pkey = paramiko.RSAKey.from_private_key(StringIO(self._server['ssh']['key']))
                    self._tunnel = sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_pkey=pkey, remote_bind_address=(self._server['sql']['hostname'], self._server['sql']['port']))
                    self._tunnel.start()

                # Start SQL Connection
                hostname = '127.0.0.1' if self._server['ssh']['enabled'] else self._server['sql']['hostname']
                port = self._tunnel.local_bind_port if self._server['ssh']['enabled'] else self._server['sql']['port']
                database = self._server['sql']['database'] if 'database' in self._server['sql'] else None
                self._sql = pymysql.connect(host=hostname, port=port, user=self._server['sql']['username'], passwd=self._server['sql']['password'], database=database, charset='utf8mb4', use_unicode=True, autocommit=False, client_flag=CLIENT.MULTI_STATEMENTS)
                self.execute('SET wait_timeout = 10')
                self._connection_id = self.execute('SELECT CONNECTION_ID()')['data'][0]['CONNECTION_ID()']
                return
            except Exception as e:
                self.close()
                error = e
                time.sleep(1)

            finally:
                # Show Errors Output Again
                sys.stderr = sys_stderr

        # Check errors
        if error is not None:
            self.close()
            raise error

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
            self._tunnel.stop()
        except Exception:
            pass

    def execute(self, query, args=None, database=None, fetch=True):
        try:
            try:
                self._sql.ping(reconnect=False)
            except Exception as e:
                self.connect()

            # Execute the query and return results
            self._is_executing = True
            return self.__execute_query(query, args, database, fetch)

        except (pymysql.ProgrammingError, pymysql.IntegrityError, pymysql.InternalError, pymysql.OperationalError) as error:
            raise Exception(error.args[1])

        finally:
            self._last_execution = time.time()
            self._is_executing = False

    def __execute_query(self, query, args, database, fetch):
        # Select the database
        if database:
            self._sql.select_db(database)

        # Prepare the cursor
        if fetch:
            with self._sql.cursor(OrderedDictCursor) as cursor:            
                # Execute the SQL query ignoring warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    start_time = time.time()
                    cursor.execute(query, args)

                # Get the query results
                data = cursor.fetchall()

            # Return query info
            query_data = {"data": data, "lastRowId": cursor.lastrowid, "rowCount": cursor.rowcount, "time": "{0:.3f}".format(time.time() - start_time)}
            return query_data
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._cursor = self._sql.cursor(OrderedDictCursor)
                self._cursor.execute(query, args)

    def fetch_one(self):
        if self._cursor:
            return self._cursor.fetchone()

    def fetch_many(self, size):
        if self._cursor:
            return self._cursor.fetchmany(size=None)

    def begin(self):
        self._sql.begin()

    def commit(self):
        self._sql.commit()

    def rollback(self):
        try:
            self._sql.rollback()
        except Exception:
            pass

    def mogrify(self, query, args):
        with self._sql.cursor(OrderedDictCursor) as cursor:    
            return cursor.mogrify(query, args)
    
    def kill(self, connection_id):
        try:
            self.execute('CALL mysql.rds_kill_query({})'.format(connection_id))
        except Exception:
            self.execute('KILL QUERY {}'.format(connection_id))

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
            SELECT schema_name AS 'name', default_character_set_name AS 'encoding', default_collation_name AS 'collation'
            FROM information_schema.schemata
        """
        result = self.execute(query)['data']
        return result

    def get_all_tables(self, db):
        query = """
            SELECT table_name AS 'name', IF(table_type = 'VIEW', 'view','table') AS 'type'
            FROM information_schema.tables 
            WHERE table_schema = %s
        """
        return self.execute(query, args=(db))['data']

    def get_all_columns(self, db):
        query = """
            SELECT DISTINCT column_name AS 'name', column_type AS 'type'
            FROM information_schema.columns
            WHERE table_schema = %s
        """
        return self.execute(query, args=(db))['data']

    def get_all_triggers(self, db):
        query = """
            SELECT trigger_name AS 'name'
            FROM information_schema.triggers
            WHERE trigger_schema = %s
        """
        return self.execute(query, args=(db))['data']

    def get_all_events(self, db):
        query = """
            SELECT event_name AS 'name'
            FROM information_schema.events
            WHERE event_schema = %s;
        """
        return self.execute(query, args=(db))['data']

    def get_all_routines(self, db):
        query = """
            SELECT routine_name AS 'name', LOWER(routine_type) AS 'type'
            FROM information_schema.routines
            WHERE routine_schema = %s
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
            SELECT c.constraint_name AS 'Name', column_name AS 'Column', k.referenced_table_schema AS 'FK Database', k.referenced_table_name AS 'FK Table', referenced_column_name AS 'FK Column', update_rule AS 'On Update', delete_rule AS 'On Delete'
            FROM information_schema.KEY_COLUMN_USAGE k
            JOIN information_schema.REFERENTIAL_CONSTRAINTS c ON c.constraint_name = k.constraint_name AND c.constraint_schema = k.constraint_schema
            WHERE c.constraint_schema = %s
            AND k.table_name = %s
        """
        return self.execute(query, args=(db, table))['data']
    
    def get_triggers(self, db, table):
        query = """
            SELECT trigger_name AS 'Name', action_timing AS 'Timing', action_statement AS 'Statement', event_manipulation AS 'Event', definer AS 'Definer', created AS 'Created', character_set_client AS 'Character Set Client', collation_connection AS 'Collation Connection', database_collation AS 'Database Collation'
            FROM information_schema.triggers
            WHERE event_object_schema = %s
            AND event_object_table = %s
        """
        return self.execute(query, args=(db, table))['data']

    def get_databases(self, db_regex):
        query = "SELECT DISTINCT(table_schema) AS table_schema FROM information_schema.tables WHERE table_schema LIKE '" + db_regex.strip() + "'"
        result = self.execute(query)['data']

        databases = []
        for db in result:
            databases.append(db['table_schema'])
        return databases

    def get_table_size(self, db, table):
        query = "SELECT (data_length + index_length)/1024/1024 AS table_size FROM information_schema.tables WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\""
        result = self.execute(query)['data']
        return result[0]['table_size']

    def check_db_exists(self, db):
        query = "SELECT COUNT(*) AS count FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = \"" + db.strip() + "\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_table_exists(self, db, table):
        query = "SELECT COUNT(*) AS count FROM information_schema.tables WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_column_exists(self, db, table, column):
        query = "SELECT COUNT(*) AS count FROM information_schema.columns WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND column_name = \"" + column.strip() + "\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_index_exists(self, db, table, index):
        query = "SELECT COUNT(*) AS count FROM information_schema.statistics WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND index_name = \"" + index.strip() + "\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) > 0 else False

    def check_pk_exists(self, db, table):
        query = "SELECT COUNT(*) AS count FROM information_schema.statistics WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND index_name = \"PRIMARY\""
        result = self.execute(query)['data']
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
        result = self.execute(query)['data']
        return True if int(result[0]['exist']) == 1 else False

    def check_fk_exists(self, db, table, column):
        query = "SELECT COUNT(*) AS count FROM information_schema.key_column_usage WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND column_name = \"" + column.strip() + "\" AND referenced_table_name IS NOT NULL"
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_fk_exists_by_name(self, db, table, foreign):
        query = "SELECT COUNT(*) AS count FROM information_schema.key_column_usage WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND constraint_name = \"" + foreign.strip() + "\" AND referenced_table_name IS NOT NULL"
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_partition_exists(self, db, table, partition):
        query = "SELECT COUNT(*) AS count FROM information_schema.partitions WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND partition_name = \"" + partition.strip() + "\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_trigger_exists(self, db, table, trigger):
        query = "SELECT COUNT(*) AS count FROM information_schema.triggers WHERE event_object_schema = \"" + db.strip() + "\" AND event_object_table LIKE \"" + table.strip() + "\" AND trigger_name = \"" + trigger.strip() + "\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_view_exists(self, db, view):
        query = "SELECT COUNT(*) AS count FROM information_schema.views WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + view.strip() + "\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_function_exists(self, db, function):
        query = "SELECT COUNT(*) AS count FROM information_schema.routines WHERE routine_schema = \"" + db.strip() + "\" AND routine_name = \"" + function.strip() + "\" AND routine_type = \"FUNCTION\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_procedure_exists(self, db, procedure):
        query = "SELECT COUNT(*) AS count FROM information_schema.routines WHERE routine_schema = \"" + db.strip() + "\" AND routine_name = \"" + procedure.strip() + "\" AND routine_type = \"PROCEDURE\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_event_exists(self, event):
        query = "SELECT COUNT(*) AS count FROM information_schema.events WHERE EVENT_NAME = \"" + event.strip() + "\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def check_user_exists(self, user, host):
        query = "SELECT COUNT(*) AS count FROM mysql.user WHERE User = \"" + user + "\" AND Host = \"" + host.strip() + "\""
        result = self.execute(query)['data']
        return True if int(result[0]['count']) == 1 else False

    def get_row_format(self, db, table):
        query = "SELECT row_format AS row_format FROM information_schema.tables WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\""
        result = self.execute(query)['data']
        return result[0]['row_format']

    def get_column_names(self, db, table):
        query = "SELECT COLUMN_NAME, COLUMN_DEFAULT, DATA_TYPE FROM information_schema.columns WHERE table_schema = '" + db.strip() + "' AND table_name = '" + table.strip() + "' ORDER BY ordinal_position"
        result = self.execute(query)['data']

        columns = {'name': [], 'default': [], 'type': {}}
        for cl in result:
            columns['name'].append(cl['COLUMN_NAME'])
            columns['default'].append(cl['COLUMN_DEFAULT'])
            columns['type'][cl['COLUMN_NAME']] = cl['DATA_TYPE']
        return columns

    def get_pk_names(self, db, table):
        query = "SELECT COLUMN_NAME FROM information_schema.statistics WHERE table_schema = '" + db.strip() + "' AND table_name = '" + table.strip() + "' AND index_name = 'PRIMARY'"
        result = self.execute(query)['data']
        
        columns = []
        for cl in result:
            columns.append(cl['COLUMN_NAME'])
        return columns

    def get_database_info(self):
        query = """
            SELECT schema_name AS 'name', default_character_set_name AS 'charset', default_collation_name AS 'collation'
            FROM information_schema.schemata
        """
        result = self.execute(query)['data']
        return result

    def get_table_info(self, db, table=None):
        table = '' if table is None else "AND t.table_name = '{}'".format(table)
        query = """
            SELECT table_name AS 'name', table_rows AS 'rows', data_length, index_length, (data_length + index_length) AS 'total_length', engine, row_format, avg_row_length, data_free, auto_increment, c.character_set_name AS 'charset', table_collation AS 'collation', table_comment AS 'comment', create_time AS 'created', update_time AS 'modified'
            FROM information_schema.tables t
            JOIN information_schema.collations c ON c.collation_name = t.table_collation
            WHERE t.table_schema = '{}'
            {}
            ORDER BY table_name
        """.format(db, table).strip()
        result = self.execute(query)['data']
        return result

    def get_table_syntax(self, db, table):
        query = "SHOW CREATE TABLE {}.{}".format(db, table)
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
        query = "SHOW CREATE VIEW {}.{}".format(db, view)
        result = self.execute(query)['data'][0]['Create View']
        return result

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
        query = "SHOW CREATE TRIGGER {}.{}".format(db, trigger)
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
        query = "SHOW CREATE FUNCTION {}.{}".format(db, function)
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
        query = "SHOW CREATE PROCEDURE {}.{}".format(db, procedure)
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
        query = "SHOW CREATE EVENT {}.{}".format(db, event)
        result = self.execute(query)['data'][0]['Create Event']
        return result

    def get_columns_definition(self, db, table):
        query = """
            SELECT CONCAT(column_name, ' ', column_type) AS 'column'
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = %s;
        """
        result = self.execute(query, args=(db, table))['data']

        columns = []
        for c in result:
            columns.append(c['column'])
        return columns

    def get_all_rights(self):
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
