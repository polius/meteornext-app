class Monitoring_Queries:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user):
        query = """
            SELECT s.name AS 'server', q.id, q.query_text AS 'query', q.db, q.user, q.host, q.first_seen, q.last_seen, q.execution_time, q.count
            FROM monitoring_queries q
            JOIN monitoring m ON m.server_id = q.server_id AND m.user_id = %s
            JOIN servers s ON s.id = q.server_id
            ORDER BY q.count DESC, q.execution_time DESC
            LIMIT 1000
        """
        return self._sql.execute(query, (user['id']))
