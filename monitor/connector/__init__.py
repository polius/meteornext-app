from connector.mysql import MySQL

class Connector:
    def __init__(self, config):
        if config['sql']['engine'] in ['MySQL','Amazon Aurora (MySQL)']:
            self._sql = MySQL(config)

    def connect(self):
        self._sql.connect()

    def stop(self):
        self._sql.stop()

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
