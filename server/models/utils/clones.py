class Clones:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def get(self, user_id=None, clone_uri=None):
        if clone_uri:
            query = """
                SELECT c.*, s.name AS 'source_server_name', s.shared AS 'source_server_shared', s.secured AS 'source_server_secured', s2.name AS 'destination_server_name', s2.shared AS 'destination_server_shared', s2.secured AS 'destination_server_secured', q.queue
                FROM clones c
                JOIN servers s ON s.id = c.source_server
                JOIN servers s2 ON s2.id = c.destination_server
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
                ) q ON q.source_id = c.id AND q.source_type = 'clone'
                WHERE c.uri = %s
            """
            return self._sql.execute(query, (clone_uri))
        else:
            query = """
                SELECT c.*, s.name AS 'source_server_name', s.shared AS 'source_server_shared', s.secured AS 'source_server_secured', s2.name AS 'destination_server_name', s2.shared AS 'destination_server_shared', s2.secured AS 'destination_server_secured', q.queue
                FROM clones c
                JOIN servers s ON s.id = c.source_server
                JOIN servers s2 ON s2.id = c.destination_server
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
                ) q ON q.source_id = c.id AND q.source_type = 'clone'
                WHERE c.user_id = %s
                AND c.deleted = 0
                ORDER BY c.id DESC
            """
            return self._sql.execute(query, (user_id))

    def post(self, user, data):
        query = """
            INSERT INTO clones (`source_server`, `source_database`, `destination_server`, `destination_database`, `create_database`, `recreate_database`, `mode`, `tables`, `export_schema`, `export_data`, `add_drop_table`, `export_triggers`, `export_routines`, `export_events`, `size`, `status`, `created`, `url`, `uri`, `user_id`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (data['source_server'], data['source_database'], data['destination_server'], data['destination_database'], data['create_database'], data['recreate_database'], data['mode'], data['tables'], data['export_schema'], data['export_data'], data['add_drop_table'], data['export_triggers'], data['export_routines'], data['export_events'], data['size'], data['status'], data['created'], data['url'], data['uri'], user['id']))

    def delete(self, user, item):
        query = """
            UPDATE clones
            SET deleted = 1
            WHERE uri = %s
            AND user_id = %s
        """
        self._sql.execute(query, (item, user['id']))

    def stop(self, user, clone_uri):
        query = """
            UPDATE clones
            SET `stop` = 1
            WHERE `user_id` = %s
            AND `uri` = %s
        """
        return self._sql.execute(query, (user['id'], clone_uri))

    def update_status(self, user, clone_id, status, error=None):
        query = """
            UPDATE clones
            SET
                status = %s,
                error = IF(%s IS NULL, error, %s)
            WHERE id = %s
            AND user_id = %s
        """
        return self._sql.execute(query, (status, error, error, clone_id, user['id']))
