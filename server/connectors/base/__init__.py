from connectors.base.mysql import MySQL

class Base:
    def __init__(self, config):
        if config['sql']['engine'] in ['MySQL','Aurora MySQL']:
            self._sql = MySQL(config)

    def connect(self):
        self._sql.connect()

    def close(self):
        self._sql.close()

    def test_sql(self):
        self._sql.test_sql()

    def test_ssh(self):
        self._sql.test_ssh()

    def execute(self, query, args=None, database=None):
        return self._sql.execute(query, args, database)

    def mogrify(self, query, args=None):
        return self._sql.mogrify(query, args)

    ####################
    # INTERNAL METHODS #
    ####################
    def check_db_exists(self, db):
        self._sql.check_db_exists(db)
