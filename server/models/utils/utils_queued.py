class Utils_Queued:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def build(self):
        query = """
            INSERT IGNORE INTO utils_queued (source_id, source_type)
            SELECT source_id, source_type
            FROM (
                SELECT id AS 'source_id', 'import' AS 'source_type', created
                FROM imports
                WHERE status = 'QUEUED'
                UNION ALL
                SELECT id AS 'source_id', 'import' AS 'source_type', created
                FROM exports
                WHERE status = 'QUEUED'
                UNION ALL
                SELECT id AS 'source_id', 'import' AS 'source_type', created
                FROM clones
                WHERE status = 'QUEUED'
                ORDER BY created
            ) t
        """
        self._sql.execute(query)

    def get_finished(self):
        query = """
            SELECT q.source_id, q.source_type
            FROM utils_queued q
            JOIN imports i ON i.id = q.source_id AND q.source_type = 'import' AND i.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            UNION ALL
            SELECT q.source_id, q.source_type
            FROM utils_finished q
            JOIN exports e ON e.id = q.source_id AND q.source_type = 'export' AND e.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            UNION ALL
            SELECT q.source_id, q.source_type
            FROM utils_finished q
            JOIN clones c ON c.id = q.source_id AND q.source_type = 'clone' AND c.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
        """
        return self._sql.execute(query)

    def get_next(self):
        query = """
            SELECT q.source_id, q.source_type, i.status, i.created, g.id AS 'group', COALESCE(g.utils_concurrent,100) AS 'concurrent'
            FROM utils_queued q
            JOIN imports i ON i.id = q.source_id AND q.source_type = 'import' AND i.status IN('QUEUED','STARTING','IN PROGRESS','STOPPING')
            JOIN users u ON u.id = i.user_id
            JOIN groups g ON g.id = u.group_id
            UNION ALL
            SELECT q.source_id, q.source_type, e.status, e.created, g.id AS 'group', COALESCE(g.utils_concurrent,100) AS 'concurrent'
            FROM utils_queued q
            JOIN exports e ON e.id = q.source_id AND q.source_type = 'export' AND e.status IN('QUEUED','STARTING','IN PROGRESS','STOPPING')
            JOIN users u ON u.id = e.user_id
            JOIN groups g ON g.id = u.group_id
            UNION ALL
            SELECT q.source_id, q.source_type, c.status, c.created, g.id AS 'group', COALESCE(g.utils_concurrent,100) AS 'concurrent'
            FROM utils_queued q
            JOIN clones c ON c.id = q.source_id AND q.source_type = 'clone' AND c.status IN('QUEUED','STARTING','IN PROGRESS','STOPPING')
            JOIN users u ON u.id = c.user_id
            JOIN groups g ON g.id = u.group_id
            ORDER BY created
        """
        return self._sql.execute(query)

    def get_queued_imports(self, import_ids):
        query = """
            SELECT i.id, i.mode, i.source, i.format, i.selected, i.size, i.server_id, i.database, i.create_database, i.drop_database, i.url, i.uri, u.id AS 'user_id', u.username, g.id AS 'group_id', g.utils_slack_enabled AS 'slack_enabled', g.utils_slack_url AS 'slack_url'
            FROM imports i
            JOIN users u ON u.id = i.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE i.id IN ({})
        """.format(','.join(['%s'] * len(import_ids)))
        return self._sql.execute(query, (import_ids))

    def delete(self, items):
        for i in items:
            query = """
                DELETE FROM utils_queued
                WHERE source_id = %s
                AND source_type = %s
            """
            self._sql.execute(query, args=(i['source_id'], i['source_type']))
