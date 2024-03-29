from connectors.pool.mysql import MySQL

class Pool:
    def __init__(self, config):
        self._config = config
        if config['engine'] in ['MySQL','Amazon Aurora (MySQL)']:
            self._sql = MySQL(config)

    @property
    def config(self):
        return self._config

    def execute(self, query, args=None, database=None):
        return self._sql.execute(query, args, database)

    def mogrify(self, query, args=None):
        return self._sql.mogrify(query, args)

    def raw(self, transaction=True):
        return self._sql.raw(transaction)
