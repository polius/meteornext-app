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
                WHERE r.id = %s
            """
            return self._sql.execute(query, (restore_id))
        else:
            query = """
                SELECT r.*, s.name AS 'server'
                FROM restore r
                JOIN servers s ON s.id = r.server_id
                WHERE r.user_id = %s
                AND deleted = 0
                ORDER BY r.id DESC
            """
            return self._sql.execute(query, (user_id))

    def post(self, user, data):
        query = """
            INSERT INTO restore (`mode`, `source`, `selected`, `size`, `server_id`, `database`, `created`, `uri`, `user_id`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (data['mode'], data['source'], data['selected'], data['size'], data['server_id'], data['database'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), data['uri'], user['id']))

    def delete(self, user, item):
        query = """
            UPDATE restore
            SET deleted = 1
            WHERE id = %s
            AND user_id = %s
        """
        self._sql.execute(query, (item, user['id']))

    def get_servers(self, user):
        query = """
            SELECT s.id, s.name, s.shared
            FROM servers s
            WHERE (s.shared = 1 OR s.owner_id = %s)
            AND s.usage LIKE '%%U%%'
        """
        return self._sql.execute(query, (user['id']))

    def update_status(self, user, restore_id, status):
        query = """
            UPDATE restore
            SET status = %s
            WHERE user_id = %s
            AND id = %s
        """
        return self._sql.execute(query, (status, user['id'], restore_id))
