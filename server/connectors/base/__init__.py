from connectors.base.mysql import MySQL

class Base:
    def __init__(self, config):
        if config['sql']['engine'] in ['MySQL','Aurora MySQL']:
            self._sql = MySQL(config)

    def connect(self):
        self._sql.connect()

    def stop(self):
        self._sql.stop()

    def test_sql(self):
        self._sql.test_sql()

    def test_ssh(self):
        self._sql.test_ssh()

    def use(self, database):
        self._sql.use(database)

    def execute(self, query, args=None, database=None):
        return self._sql.execute(query, args, database)

    def mogrify(self, query, args=None):
        return self._sql.mogrify(query, args)

    ####################
    # INTERNAL METHODS #
    ####################
    def get_variables(self):
        return self._sql.get_variables()

    def get_status(self):
        return self._sql.get_status()

    def get_processlist(self):
        return self._sql.get_processlist()

    def get_databases(self):
        return self._sql.get_databases()

    def get_database_size(self, database):
        return self._sql.get_database_size(database)

    def get_tables_detailed(self, database):
        return self._sql.get_tables_detailed(database)
