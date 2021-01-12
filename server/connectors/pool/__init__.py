from connectors.pool.mysql import MySQL

class Pool:
    def __init__(self, config):
        if config['sql']['engine'] in ['MySQL','Aurora MySQL']:
            self._sql = MySQL(config)

    def execute(self, query, args=None, database=None):
        return self._sql.execute(query, args, database)
