class Monitoring:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id, server_id=None):
        if server_id:
            query = """
                SELECT m.*, s.name, s.hostname, r.name AS 'region'
                FROM monitoring m
                JOIN servers s ON s.id = m.server_id AND s.id = %s
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            """
            return self._sql.execute(query, (server_id, group_id))
        else:
            query = """
                SELECT m.*
                FROM monitoring m
                JOIN servers s ON s.id = m.server_id
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            """
            return self._sql.execute(query, (group_id))

    def put(self, group_id, data):
        if len(data) == 0:
            query = """
                UPDATE monitoring
                JOIN servers s ON s.id = monitoring.server_id
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s
                SET monitor_enabled = 0
            """
            self._sql.execute(query, (group_id))
        else:
            query = """
                UPDATE monitoring
                JOIN servers s ON s.id = monitoring.server_id
                JOIN regions r ON r.id = s.region_id AND r.group_id = {}
                SET monitor_enabled = 0
                WHERE server_id NOT IN ({})
            """.format(group_id, ','.join(['%s'] * len(data)))
            self._sql.execute(query, (data))
            
            for i in data:
                query = """
                    INSERT INTO monitoring (server_id, monitor_enabled)
                    SELECT s.id, 1
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id
                    WHERE s.id = %s
                    ON DUPLICATE KEY UPDATE monitor_enabled = 1
                """
                self._sql.execute(query, (i))

    def get_monitoring(self, group_id):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name', s.hostname, (m.server_id IS NOT NULL AND m.monitor_enabled = 1) AS 'selected', m.summary, m.updated
            FROM servers s
            LEFT JOIN monitoring m ON m.server_id = s.id AND m.monitor_enabled = 1
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            ORDER BY r.name, s.name
        """
        return self._sql.execute(query, (group_id))

    def get_parameters(self, group_id):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name', s.hostname, (m.server_id IS NOT NULL AND m.parameters_enabled = 1) AS 'selected', m.parameters, m.updated
            FROM servers s
            LEFT JOIN monitoring m ON m.server_id = s.id AND m.parameters_enabled = 1
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            ORDER BY r.name, s.name
        """
        return self._sql.execute(query, (group_id))

    def get_processlist(self, group_id):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name', s.hostname, (m.server_id IS NOT NULL AND m.processlist_enabled = 1) AS 'selected', m.processlist, m.updated
            FROM servers s
            LEFT JOIN monitoring m ON m.server_id = s.id AND m.processlist_enabled = 1
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            ORDER BY r.name, s.name
        """
        return self._sql.execute(query, (group_id))

    def put_parameters(self, group_id, data):
        if len(data) == 0:
            query = """
                UPDATE monitoring
                JOIN servers s ON s.id = monitoring.server_id
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s
                SET parameters_enabled = 0
            """
            self._sql.execute(query, (group_id))
        else:
            query = """
                UPDATE monitoring
                JOIN servers s ON s.id = monitoring.server_id
                JOIN regions r ON r.id = s.region_id AND r.group_id = {}
                SET parameters_enabled = 0
                WHERE server_id NOT IN ({})
            """.format(group_id, ','.join(['%s'] * len(data)))
            self._sql.execute(query, (data))
            
            for i in data:
                query = """
                    INSERT INTO monitoring (server_id, parameters_enabled)
                    SELECT s.id, 1
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id
                    WHERE s.id = %s
                    ON DUPLICATE KEY UPDATE parameters_enabled = 1
                """
                self._sql.execute(query, (i))
