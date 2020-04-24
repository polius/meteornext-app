class Monitoring_Settings:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user):
        query = """
            SELECT *
            FROM monitoring_settings
            WHERE user_id = %s
        """
        return self._sql.execute(query, (user['id']))

    def put(self, user, data):
        query = """
            INSERT INTO monitoring_settings (user_id, monitor_align, monitor_interval)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE monitor_align = %s, monitor_interval = %s
        """
        return self._sql.execute(query, (user['id'], data['align'], data['interval'], data['align'], data['interval']))
