from mysql import mysql

class connector:
    def __init__(self, server):
        self._sql = None

        if server['sql']['engine'] == 'MySQL':
            self._sql = mysql(server)

    def start(self):
        self._sql.start()

    def stop(self):
        self._sql.stop()

    def execute(self, query, args=None, database=None):
        return self._sql.execute(query, args, database)

    def begin(self):
        self._sql.begin()

    def commit(self):
        self._sql.commit()

    def rollback(self):
        self._sql.rollback()

    ####################
    # INTERNAL QUERIES #
    ####################
    def get_parameters(self):
        return self._sql.get_parameters()

    def get_status(self):
        return self._sql.get_status()

    def get_processlist(self):
        return self._sql.get_processlist()

    def get_processlist_v2(self):
        return self._sql.get_processlist_v2()
