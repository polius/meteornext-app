class Restore:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

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
            INSERT INTO restore (`mode`, `details`, `source`, `selected`, `size`, `server_id`, `database`, `create_database`, `status`, `started`, `uri`, `upload`, `user_id`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (data['mode'], data['details'], data['source'], data['selected'], data['size'], data['server_id'], data['database'], data['create_database'], data['status'], data['started'], data['uri'], data['upload'], user['id']))

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
            SELECT s.id, s.name, s.shared, t.id IS NOT NULL AS 'active'
            FROM servers s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = 1)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            WHERE s.group_id = %(group_id)s
            AND (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%U%%'
            ORDER BY s.name
        """
        return self._sql.execute(query, {"user_id": user['id'], "group_id": user['group_id'], "license": self._license.resources})

    def stop(self, user, restore_id):
        query = """
            UPDATE restore
            SET `stop` = 1
            WHERE `user_id` = %s
            AND `id` = %s
        """
        return self._sql.execute(query, (user['id'], restore_id))
