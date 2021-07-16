from datetime import datetime

class Restore:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id=None, restore_id=None):
        if restore_id:
            query = """
                SELECT r.*, s.name AS 'server'
                FROM restore r
                JOIN servers s ON s.id = r.server_id
                WHERE r.user_id = %s
                AND r.id = %s
            """
            return self._sql.execute(query, (user_id, restore_id))
        else:
            query = """
                SELECT r.*, s.name AS 'server'
                FROM restore r
                JOIN servers s ON s.id = r.server_id
                WHERE r.user_id = %s
            """
            return self._sql.execute(query, (user_id))

    def post(self, user_id, data):
        query = """
            INSERT INTO restore (mode, source, server_id, database, created, pid, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (data['mode'], data['source'], data['server_id'], data['database'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), data['pid'], user_id))

    def put_name(self, user, data):
        query = """
            UPDATE restore
            SET name = %s
            WHERE id = %s
            AND user_id = %s
        """
        self._sql.execute(query, (data['name'], data['id'], user['id']))

    def get_servers(self, user):
        query = """
            SELECT s.id, s.name, s.shared
            FROM servers s
            WHERE (s.shared = 1 OR s.owner_id = %s)
            AND s.usage LIKE '%%U%%'
        """
        return self._sql.execute(query, (user['id']))
