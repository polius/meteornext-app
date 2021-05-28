from datetime import datetime

class Monitoring:
    def __init__(self, sql):
        self._sql = sql

    def get_servers(self, dfilter=None, dsort=None):
        if dfilter is None and dsort is None:
            query = """
                SELECT CONCAT(available.user_id, '|', available.server_id) AS 'id', available.user_id, available.user, available.server_id, available.server, available.shared, m.server_id IS NOT NULL AS 'attached', m.date
                FROM (
                    SELECT u.id AS 'user_id', u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared
                    FROM servers s
                    JOIN groups g ON g.id = s.group_id
                    LEFT JOIN users u ON u.group_id = g.id
                    WHERE (s.shared = 1 OR u.id IS NOT NULL)
                    AND s.usage LIKE '%M%'
                ) available
                LEFT JOIN monitoring m ON m.user_id = available.user_id 
                    AND m.server_id = available.server_id
                    AND m.monitor_enabled = 1
                WHERE available.user_id IS NOT NULL
                ORDER BY m.date DESC, available.user ASC, available.server ASC
                LIMIT 1000
            """
            return self._sql.execute(query)
        else:
            user = server = attached = ''
            args = []
            sort_column = 'm.date'
            sort_order = 'DESC'
            if dfilter is not None:
                if 'user' in dfilter and dfilter['user'] is not None:
                    user = 'AND u.username = %s'
                    args.append(dfilter['user'])
                if 'server' in dfilter and dfilter['server'] is not None:
                    server = 'AND s.name = %s'
                    args.append(dfilter['server'])
                if 'attached' in dfilter and dfilter['attached'] is not None:
                    attached = 'AND m.server_id IS NOT NULL' if dfilter['attached'] == 'attached' else 'AND m.server_id IS NULL'

            if dsort is not None:
                sort_column = dsort['column']
                sort_order = 'DESC' if dsort['desc'] else 'ASC'

            query = """
                SELECT CONCAT(available.user_id, '|', available.server_id) AS 'id', available.user_id, available.user, available.server_id, available.server, available.shared, m.server_id IS NOT NULL AS 'attached', m.date
                FROM (
                    SELECT u.id AS 'user_id', u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared
                    FROM servers s
                    JOIN groups g ON g.id = s.group_id
                    LEFT JOIN users u ON u.group_id = g.id
                    WHERE (s.shared = 1 OR u.id IS NOT NULL)
                    AND s.usage LIKE '%%M%%'
                    {} {}
                ) available
                LEFT JOIN monitoring m ON m.user_id = available.user_id 
                    AND m.server_id = available.server_id
                    AND m.monitor_enabled = 1
                WHERE available.user_id IS NOT NULL {}
                ORDER BY {} {}
                LIMIT 1000
            """.format(user, server, attached, sort_column, sort_order)
            return self._sql.execute(query, args)

    def attach_servers(self, data):
        for server in data['servers']:
            query = """
                INSERT INTO monitoring (`user_id`, `server_id`, `monitor_enabled`, `date`)
                VALUES (%s, %s, 1, %s)
                ON DUPLICATE KEY UPDATE
                    `monitor_enabled` = VALUES(`monitor_enabled`),
                    `date` = VALUES(`date`)
            """
            self._sql.execute(query, (server['user_id'], server['server_id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def detach_servers(self, data):
        for server in data:
            query = """
                UPDATE monitoring
                SET 
                    monitor_enabled = 0,
                    parameters_enabled = 0,
                    processlist_enabled = 0,
                    processlist_active = 0,
                    queries_enabled = 0
                WHERE user_id = %s
                AND server_id = %s
            """
            self._sql.execute(query, (server['user_id'], server['server_id']))

    def get_users_list(self):
        query = """
            SELECT u.username AS 'user', g.name AS 'group'
            FROM users u
            JOIN groups g ON g.id = u.group_id
            ORDER BY u.username
        """
        return self._sql.execute(query)

    def get_servers_list(self):
        query = """
            SELECT DISTINCT(name) AS 'name'
            FROM servers
            ORDER BY name ASC
        """
        return [server['name'] for server in self._sql.execute(query)]
