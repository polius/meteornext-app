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

    # def post(self, group_id, se):
    #     query = """
    #         INSERT INTO monitoring (server_id)
    #     """

    def get_servers(self, group_id):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name', m.server_id IS NOT NULL AS 'selected'
            FROM servers s
            LEFT JOIN monitoring m ON m.server_id = s.id
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            ORDER BY r.name, s.name
        """
        return self._sql.execute(query, (group_id))
