class Imports:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def get(self, user_id=None, import_uri=None):
        if import_uri:
            query = """
                SELECT i.*, s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', q.queue
                FROM imports i
                JOIN servers s ON s.id = i.server_id
                LEFT JOIN
                (
                    SELECT (@cnt := @cnt + 1) AS queue, source_id, source_type
                    FROM (
                        SELECT i.id AS 'source_id', 'import' AS 'source_type', i.created
                        FROM imports i
                        WHERE i.status = 'QUEUED'
                        UNION ALL
                        SELECT e.id AS 'source_id', 'export' AS 'source_type', e.created
                        FROM exports e
                        WHERE e.status = 'QUEUED'
                        UNION ALL
                        SELECT c.id AS 'source_id', 'clone' AS 'source_type', c.created
                        FROM clones c
                        WHERE c.status = 'QUEUED'
                        ORDER BY created
                    ) t
                    JOIN (SELECT @cnt := 0) cnt
                ) q ON q.source_id = i.id AND q.source_type = 'import'
                WHERE i.uri = %s
            """
            return self._sql.execute(query, (import_uri))
        else:
            query = """
                SELECT i.*, s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', q.queue
                FROM imports i
                JOIN servers s ON s.id = i.server_id
                LEFT JOIN
                (
                    SELECT (@cnt := @cnt + 1) AS queue, source_id, source_type
                    FROM (
                        SELECT i.id AS 'source_id', 'import' AS 'source_type', i.created
                        FROM imports i
                        WHERE i.status = 'QUEUED'
                        UNION ALL
                        SELECT e.id AS 'source_id', 'export' AS 'source_type', e.created
                        FROM exports e
                        WHERE e.status = 'QUEUED'
                        UNION ALL
                        SELECT c.id AS 'source_id', 'clone' AS 'source_type', c.created
                        FROM clones c
                        WHERE c.status = 'QUEUED'
                        ORDER BY created
                    ) t
                    JOIN (SELECT @cnt := 0) cnt
                ) q ON q.source_id = i.id AND q.source_type = 'import'
                WHERE i.user_id = %s
                AND deleted = 0
                ORDER BY i.id DESC
            """
            return self._sql.execute(query, (user_id))

    def post(self, user, data):
        query = """
            INSERT INTO imports (`mode`, `details`, `source`, `format`, `selected`, `size`, `server_id`, `database`, `create_database`, `drop_database`, `status`, `created`, `url`, `uri`, `upload`, `user_id`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (data['mode'], data['details'], data['source'], data['format'], data['selected'], data['size'], data['server_id'], data['database'], data['create_database'], data['drop_database'], data['status'], data['created'], data['url'], data['uri'], data['upload'], user['id']))

    def delete(self, user, item):
        query = """
            UPDATE imports
            SET deleted = 1
            WHERE id = %s
            AND user_id = %s
        """
        self._sql.execute(query, (item, user['id']))

    def get_servers(self, user):
        query = """
            SELECT s.id, s.name, s.shared, s.secured, s.region_id, t.id IS NOT NULL AS 'active'
            FROM servers s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = %(user_id)s)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            WHERE s.group_id = %(group_id)s
            AND (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%U%%'
            ORDER BY s.name
        """
        return self._sql.execute(query, {"user_id": user['id'], "group_id": user['group_id'], "license": self._license.resources})

    def stop(self, user, import_uri):
        query = """
            UPDATE imports
            SET `stop` = 1
            WHERE `user_id` = %s
            AND `uri` = %s
        """
        return self._sql.execute(query, (user['id'], import_uri))

    def update_status(self, user, import_id, status, error=None):
        query = """
            UPDATE imports
            SET
                status = %s,
                error = IF(%s IS NULL, error, %s)
            WHERE id = %s
            AND user_id = %s
        """
        return self._sql.execute(query, (status, error, error, import_id, user['id']))
