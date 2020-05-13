class PostgreSQL:
    def __init__(self, server):
        self._server = server
        self._tunnel = None
        self._sql = None
