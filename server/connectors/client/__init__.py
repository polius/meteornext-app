import time
import threading
from connectors.client.mysql import MySQL

class Client:
    def __init__(self, app):
        self._connections = {}

        @app.before_first_request
        def start():
            ttl = 60
            t = threading.Thread(target=self.__scheduler, args=(ttl,))
            t.start()

    def __scheduler(self, ttl):
        while True:
            self.__close_active_connections(ttl)
            time.sleep(10)

    def __close_active_connections(self, ttl):
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
        if total > 0:
            pass
            # print("- [CLIENT] Connections closed: {}".format(total))

    def connect(self, user_id, conn_id, server):
        user_id = int(user_id)
        conn_id = str(conn_id)
        if user_id not in self._connections or conn_id not in self._connections[user_id] or server['id'] != self._connections[user_id][conn_id].server['id']:
            conn = Connection(server)
            conn.connect()
            if user_id not in self._connections:
                self._connections[user_id] = {} 
            self._connections[user_id][conn_id] = conn
        self._connections[user_id][conn_id].is_protected = True
        return self._connections[user_id][conn_id]

    def kill(self, user_id, conn_id):
        try:
            connection = self._connections[int(user_id)][str(conn_id)]
            conn = Connection(connection.server)
            conn.kill(connection.connection_id)
        except Exception:
            pass

    def close(self, user_id, conn_id):
        try:
            user_id = int(user_id)
            conn_id = str(conn_id)
            for conn_name in ['-main','-shared','-shared2']: 
                if user_id in self._connections and conn_id + conn_name in self._connections[user_id]:
                    connection = self._connections[user_id][conn_id + conn_name]
                    conn = Connection(connection.server)
                    conn.kill(connection.connection_id)
                    connection.close()
            self._connections[user_id].pop(conn_id, None)
        except Exception:
            pass

class Connection:
    def __init__(self, server):
        self._server = server
        if server['sql']['engine'] in ['MySQL','Aurora MySQL']:
            self._sql = MySQL(server)

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

    def connect(self):
        self._start = time.time()
        self._connection_id = self._sql.connect()

    def close(self):
        self._sql.close()

    def execute(self, query, args=None, database=None, fetch=True):
       return self._sql.execute(query, args, database, fetch)

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

    def get_databases(self, db_regex):
        return self._sql.get_databases(db_regex)

    def get_table_size(self, db, table):
        return self._sql.get_table_size(db, table)
       
    def check_db_exists(self, db):
        return self._sql.check_db_exists(db)
       
    def check_table_exists(self, db, table):
        return self._sql.check_table_exists(db, table)
       
    def check_column_exists(self, db, table, column):
        return self._sql.check_column_exists(db, table, column)
      
    def check_index_exists(self, db, table, index):
        return self._sql.check_index_exists(db, table, index)
        
    def check_pk_exists(self, db, table):
        return self._sql.check_pk_exists(db, table)
       
    def check_pk_exists_columns(self, db, table, columns):
        return self._sql.check_pk_exists_columns(db, table, columns)

    def check_fk_exists(self, db, table, column):
        return self._sql.check_fk_exists(db, table, column)
       
    def check_fk_exists_by_name(self, db, table, foreign):
        return self._sql.check_fk_exists_by_name(db, table, foreign)
       
    def check_partition_exists(self, db, table, partition):
        return self._sql.check_partition_exists(db, table, partition)
        
    def check_trigger_exists(self, db, table, trigger):
        return self._sql.check_trigger_exists(db, table, trigger)
        
    def check_view_exists(self, db, view):
        return self._sql.check_view_exists(db, view)
        
    def check_function_exists(self, db, function):
        return self._sql.check_function_exists(db, function)
        
    def check_procedure_exists(self, db, procedure):
        return self._sql.check_procedure_exists(db,  procedure)
        
    def check_event_exists(self, event):
        return self._sql.check_event_exists(event)
        
    def check_user_exists(self, user, host):
        return self._sql.check_user_exists(user, host)
        
    def get_row_format(self, db, table):
        return self._sql.get_row_format(db, table)
        
    def get_column_names(self, db, table):
        return self._sql.get_column_names(db, table)

    def get_pk_names(self, db, table):
        return self._sql.get_pk_names(db, table)

    def get_database_info(self):
        return self._sql.get_database_info()

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
