import time
import threading
from connectors.client.mysql import MySQL

class Client:
    def __init__(self):
        self._connections = {}
        self._started = False

    def get(self, user_id, conn_id):
        try:
            return self._connections[user_id][conn_id]
        except KeyError:
            return None

    def connect(self, user_id, conn_id, server):
        if not self._started:
            self._started = True
            t = threading.Thread(target=self.__close_active_connections)
            t.daemon = True
            t.start()

        user_id = int(user_id)
        conn_id = str(conn_id)
        if user_id not in self._connections or conn_id not in self._connections[user_id] or server['id'] != self._connections[user_id][conn_id].server['id']:
            conn = Connection(server)
            conn.connect()
            if user_id not in self._connections:
                self._connections[user_id] = {} 
            self._connections[user_id][conn_id] = conn
        self._connections[user_id][conn_id].is_protected = True
        self._connections[user_id][conn_id].server = server
        return self._connections[user_id][conn_id]

    def kill(self, user_id, conn_id):
        try:
            connection = self._connections[int(user_id)][str(conn_id)]
            connection.stop_timeout()
            conn = Connection(connection.server)
            conn.connect()
            conn.kill(connection.connection_id)
            conn.close()
        except Exception:
            pass

    def close(self, user_id, conn_id):
        try:
            user_id = int(user_id)
            conn_id = str(conn_id)
            for conn_name in ['-main','-shared','-shared2','-clone']:
                if user_id in self._connections and conn_id + conn_name in self._connections[user_id]:
                    connection = self._connections[user_id][conn_id + conn_name]
                    conn = Connection(connection.server)
                    conn.kill(connection.connection_id)
                    connection.close()
            self._connections[user_id].pop(conn_id, None)
        except Exception:
            pass

    def __close_active_connections(self):
        ttl = 300
        while True:
            now = time.time()
            total = 0
            collector = {k:[k2 for k2,v2 in v.items() if (not v2.is_protected and not v2.is_executing and ((not v2.is_transaction and v2.last_execution + ttl < now) or (v2.is_transaction and v2.last_execution + 3600 < now)))] for k,v in self._connections.items()}
            for user_id, connections in collector.items():
                for conn_id in connections:
                    self._connections[user_id][conn_id].close()
                    self._connections[user_id].pop(conn_id, None)
                    total += 1
            for user_id in collector.keys():
                if len(self._connections[user_id]) == 0:
                    self._connections.pop(user_id, None)
            time.sleep(10)

class Connection:
    def __init__(self, server):
        self._server = server
        self._client_query_id = None
        if server['sql']['engine'] in ['MySQL','Amazon Aurora (MySQL)']:
            self._sql = MySQL(server)

    @property
    def query_id(self):
        return self._client_query_id

    @query_id.setter
    def query_id(self, value):
        self._client_query_id = value

    @property
    def start_execution(self):
        return self._sql.start_execution

    @property
    def last_execution(self):
        return self._sql.last_execution

    @property
    def is_executing(self):
        return self._sql.is_executing

    @property
    def is_protected(self):
        return self._sql.is_protected

    @is_protected.setter
    def is_protected(self, value):
        self._sql.is_protected = value

    @property
    def is_transaction(self):
        return self._sql.is_transaction

    @property
    def connection_id(self):
        return self._sql.connection_id

    @property
    def last_execution(self):
        return self._sql.last_execution

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, value):
        self._sql.server = value

    def connect(self):
        self._start_time = time.time()
        self._connection_id = self._sql.connect()

    def close(self):
        self._sql.close()

    def execute(self, query, args=None, database=None, fetch=True, import_file=False):
        return self._sql.execute(query, args, database, fetch, import_file)

    def fetch_one(self):
        return self._sql.fetch_one()
    
    def fetch_many(self, size=None):
        return self._sql.fetch_many(size)

    def begin(self):
        self._sql.begin()

    def commit(self):
        self._sql.commit()

    def rollback(self):
        self._sql.rollback()

    def mogrify(self, query, args):
        return self._sql.mogrify(query, args)

    def kill(self, connection_id):
        self._sql.kill(connection_id)

    def explain(self, query, database=None):
        return self._sql.explain(query, database)

    def stop_timeout(self):
        self._sql.stop_timeout()

    ####################
    # INTERNAL QUERIES #
    ####################
    def get_server_variables(self):
        return self._sql.get_server_variables()

    def get_default_encoding(self):
        return self._sql.get_default_encoding()

    def get_default_collation(self):
        return self._sql.get_default_collation()

    def get_version(self):
        return self._sql.get_version()

    def get_engines(self):
        return self._sql.get_engines()

    def get_encodings(self):
        return self._sql.get_encodings()

    def get_collations(self, encoding):
        return self._sql.get_collations(encoding)

    def get_all_databases(self):
        return self._sql.get_all_databases()

    def get_all_tables(self, db):
        return self._sql.get_all_tables(db)

    def get_all_columns(self, db):
        return self._sql.get_all_columns(db)

    def get_all_triggers(self, db):
        return self._sql.get_all_triggers(db)

    def get_all_events(self, db):
        return self._sql.get_all_events(db)

    def get_all_routines(self, db):
        return self._sql.get_all_routines(db)

    def get_columns(self, db, table):
        return self._sql.get_columns(db, table)

    def get_indexes(self, db, table):
        return self._sql.get_indexes(db, table)
    
    def get_fks(self, db, table):
        return self._sql.get_fks(db, table)
    
    def get_triggers(self, db, table):
        return self._sql.get_triggers(db, table)
        
    def get_column_names(self, db, table):
        return self._sql.get_column_names(db, table)

    def get_pk_names(self, db, table):
        return self._sql.get_pk_names(db, table)

    def get_table_info(self, db, table=None):
        return self._sql.get_table_info(db, table)

    def get_table_syntax(self, db, table):
        return self._sql.get_table_syntax(db, table)

    def get_view_info(self, db, view=None):
        return self._sql.get_view_info(db, view)

    def get_view_syntax(self, db, view):
        return self._sql.get_view_syntax(db, view)

    def get_trigger_info(self, db, trigger=None):
        return self._sql.get_trigger_info(db, trigger)

    def get_trigger_syntax(self, db, trigger):
        return self._sql.get_trigger_syntax(db, trigger)

    def get_function_info(self, db, function=None):
        return self._sql.get_function_info(db, function)
    
    def get_function_syntax(self, db, function):
        return self._sql.get_function_syntax(db, function)

    def get_procedure_info(self, db, procedure=None):
        return self._sql.get_procedure_info(db, procedure)

    def get_procedure_syntax(self, db, procedure):
        return self._sql.get_procedure_syntax(db, procedure)

    def get_event_info(self, db, event=None):
        return self._sql.get_event_info(db, event)

    def get_event_syntax(self, db, event):
        return self._sql.get_event_syntax(db, event)

    def get_columns_definition(self, db, table):
        return self._sql.get_columns_definition(db, table)

    def get_all_rights(self):
        return self._sql.get_all_rights()

    def get_server_rights(self, user, host):
        return self._sql.get_server_rights(user, host)

    def get_db_rights(self, user, host):
        return self._sql.get_db_rights(user, host)

    def get_table_rights(self, user, host):
        return self._sql.get_table_rights(user, host)

    def get_column_rights(self, user, host):
        return self._sql.get_column_rights(user, host)

    def get_proc_rights(self, user, host):
        return self._sql.get_proc_rights(user, host)

    def get_rights_syntax(self, user, host):
        return self._sql.get_rights_syntax(user, host)

    def enable_fks_checks(self):
        return self._sql.enable_fks_checks()

    def disable_fks_checks(self):
        return self._sql.disable_fks_checks()

    def get_table_pks(self, database, table):
        return self._sql.get_table_pks(database, table)

    def get_processlist(self):
        return self._sql.get_processlist()
