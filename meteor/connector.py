from mysqlib import MySQL

class connector:
    def __init__(self, server):
        self._sql = None

        if server['sql']['engine'] in ['MySQL','Aurora MySQL']:
            self._sql = MySQL(server)

    def start(self):
        self._sql.start()

    def stop(self):
        self._sql.stop()

    def execute(self, query, args=None, database=None, retry=True):
        return self._sql.execute(query, args, database, retry)

    def begin(self):
        self._sql.begin()

    def commit(self):
        self._sql.commit()

    def rollback(self):
        self._sql.rollback()

    ####################
    # INTERNAL QUERIES #
    ####################
    def get_all_databases(self):
        return self._sql.get_all_databases()

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
