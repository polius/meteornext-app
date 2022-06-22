class Exports:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def get(self, user_id=None, export_uri=None):
        if export_uri:
            query = """
                SELECT e.*, s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', q.queue
                FROM exports e
                JOIN servers s ON s.id = e.server_id
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
                ) q ON q.source_id = e.id AND q.source_type = 'export'
                WHERE e.uri = %s
            """
            return self._sql.execute(query, (export_uri))
        else:
            query = """
                SELECT e.*, s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', q.queue
                FROM exports e
                JOIN servers s ON s.id = e.server_id
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
                ) q ON q.source_id = e.id AND q.source_type = 'export'
                WHERE e.user_id = %s
                AND e.deleted = 0
                ORDER BY e.id DESC
            """
            return self._sql.execute(query, (user_id))

    def post(self, user, data):
        query = """
            INSERT INTO exports (`server_id`, `database`, `mode`, `tables`, `export_schema`, `export_data`, `add_drop_table`, `export_triggers`, `export_routines`, `export_events`, `size`, `status`, `created`, `url`, `uri`, `user_id`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (data['server_id'], data['database'], data['mode'], data['tables'], data['export_schema'], data['export_data'], data['add_drop_table'], data['export_triggers'], data['export_routines'], data['export_events'], data['size'], data['status'], data['created'], data['url'], data['uri'], user['id']))

    def delete(self, user, item):
        query = """
            UPDATE exports
            SET deleted = 1
            WHERE uri = %s
            AND user_id = %s
        """
        self._sql.execute(query, (item, user['id']))

    def stop(self, user, export_uri):
        query = """
            UPDATE exports
            SET `stop` = 1,
                `status` = 'STOPPING'
            WHERE `uri` = %s
            AND (1 = %s OR `user_id` = %s)
        """
        return self._sql.execute(query, (export_uri, user['admin'], user['id']))

    def update_status(self, user, export_id, status, error=None):
        query = """
            UPDATE exports
            SET
                status = %s,
                error = IF(%s IS NULL, error, %s)
            WHERE id = %s
            AND user_id = %s
        """
        return self._sql.execute(query, (status, error, error, export_id, user['id']))
