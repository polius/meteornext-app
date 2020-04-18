from datetime import datetime

class Monitoring:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id):
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
                DELETE m
                FROM monitoring m
                JOIN servers s ON s.id = m.server_id
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s 
            """
            self._sql.execute(query, (group_id))
        else:
            query = """
                DELETE m
                FROM monitoring m
                JOIN servers s ON s.id = m.server_id
                JOIN regions r ON r.id = s.region_id
                WHERE r.group_id = {}
                AND server_id NOT IN ({}) 
            """.format(group_id, ','.join(['%s'] * len(data)))
            self._sql.execute(query, (data))
            
            for i in data:
                query = """
                    INSERT IGNORE INTO monitoring (server_id)
                    SELECT s.id
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id
                    WHERE s.id = %s;
                """
                self._sql.execute(query, (i))

    def get_servers(self, group_id):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name', s.hostname, m.server_id IS NOT NULL AS 'selected', m.summary
            FROM servers s
            LEFT JOIN monitoring m ON m.server_id = s.id
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            ORDER BY r.name, s.name
        """
        return self._sql.execute(query, (group_id))
