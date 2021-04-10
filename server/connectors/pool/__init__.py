from connectors.pool.mysql import MySQL

class Pool:
    def __init__(self, config):
        if config['sql']['engine'] in ['MySQL','Aurora MySQL']:
            self._sql = MySQL(config)

    def execute(self, query, args=None, database=None, conn=None):
        return self._sql.execute(query, args, database)

    def mogrify(self, query, args=None):
        return self._sql.mogrify(query, args)

    def transaction(self):
        return self._sql.transaction()

    def commit(self, conn):
        return self._sql.commit(conn)

    def rollback(self, conn):
        return self._sql.rollback(conn)
