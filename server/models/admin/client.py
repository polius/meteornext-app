from datetime import datetime

class Client:
    def __init__(self, sql):
        self._sql = sql

    def get_queries(self, dfilter=None, dsort=None):
        if dfilter is None and dsort is None:
            query = """
                SELECT cq.id, cq.date, u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared, cq.database, cq.query, cq.status, cq.records, cq.elapsed, cq.error
                FROM client_queries cq
                JOIN users u ON u.id = cq.user_id
                JOIN servers s ON s.id = cq.server_id
                ORDER BY cq.id DESC
                LIMIT 1000
            """
            return self._sql.execute(query)
        else:
            user = server = database = query = status = date_from = date_to = ''
            args = []
            sort_column = 'cq.id'
            sort_order = 'DESC'
            if dfilter is not None:
                matching = {
                    'equal':        { 'operator': '=', 'args': '{}' },
                    'not_equal':    { 'operator': '!=', 'args': '{}' },
                    'starts':       { 'operator': 'LIKE', 'args': '%{}' },
                    'not_starts':   { 'operator': 'NOT LIKE', 'args': '%{}' },
                    'contains':     { 'operator': 'LIKE', 'args': '%{}%' },
                    'not_contains': { 'operator': 'NOT LIKE', 'args': '%{}%' }
                }
                if 'user' in dfilter and dfilter['user'] is not None:
                    user = 'AND u.username = %s'
                    args.append(dfilter['user'])
                if 'server' in dfilter and dfilter['server'] is not None:
                    server = 'AND s.name = %s'
                    args.append(dfilter['server'])
                if 'database' in dfilter and len(dfilter['database']) > 0 and 'databaseFilter' in dfilter and dfilter['databaseFilter'] in matching:
                    database = f"AND cq.database {matching[dfilter['databaseFilter']]['operator']} %s"
                    args.append(matching[dfilter['databaseFilter']]['args'].format(dfilter['database']))
                if 'query' in dfilter and len(dfilter['query']) > 0 and 'queryFilter' in dfilter and dfilter['queryFilter'] in matching:
                    query = f"AND cq.query {matching[dfilter['queryFilter']]['operator']} %s"
                    args.append(matching[dfilter['queryFilter']]['args'].format(dfilter['query']))
                if 'status' in dfilter and dfilter['status'] is not None:
                    status = 'AND cq.status = %s'
                    args.append(dfilter['status'])
                if 'dateFrom' in dfilter and len(dfilter['dateFrom']) > 0:
                    date_from = 'AND cq.date >= %s'
                    args.append(dfilter['dateFrom'])
                if 'dateTo' in dfilter and len(dfilter['dateTo']) > 0:
                    date_to = 'AND cq.date <= %s'
                    args.append(dfilter['dateTo'])

            if dsort is not None:
                sort_column = dsort['column']
                sort_order = 'DESC' if dsort['desc'] else 'ASC'

            query = """
                SELECT cq.id, cq.date, u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared, cq.database, cq.query, cq.status, cq.records, cq.elapsed, cq.error
                FROM client_queries cq
                JOIN users u ON u.id = cq.user_id
                JOIN servers s ON s.id = cq.server_id
                WHERE 1=1
                {} {} {} {} {} {} {}
                ORDER BY {} {}
                LIMIT 1000
            """.format(user, server, database, query, status, date_from, date_to, sort_column, sort_order)
            return self._sql.execute(query, args)

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

    def get_servers(self, dfilter=None, dsort=None):
        if dfilter is None and dsort is None:
            query = """
                SELECT CONCAT(available.user_id, '|', available.server_id) AS 'id', available.user_id, available.user, available.server_id, available.server, available.shared, cs.server_id IS NOT NULL AS 'attached', cs.date, cf.name AS 'folder'
                FROM (
                    SELECT u.id AS 'user_id', u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared
                    FROM servers s
                    JOIN groups g ON g.id = s.group_id
                    LEFT JOIN users u ON u.group_id = g.id
                    WHERE (s.shared = 1 OR u.id IS NOT NULL)
                    AND s.usage LIKE '%C%'
                ) available
                LEFT JOIN client_servers cs USING (user_id, server_id)
                LEFT JOIN client_folders cf ON cf.id = cs.folder_id
                WHERE available.user_id IS NOT NULL
                ORDER BY cs.date DESC, available.user ASC, available.server ASC
                LIMIT 1000
            """
            return self._sql.execute(query)
        else:
            user = server = attached = ''
            args = []
            sort_column = 'cs.date'
            sort_order = 'DESC'
            if dfilter is not None:
                if 'user' in dfilter and dfilter['user'] is not None:
                    user = 'AND u.username = %s'
                    args.append(dfilter['user'])
                if 'server' in dfilter and dfilter['server'] is not None:
                    server = 'AND s.name = %s'
                    args.append(dfilter['server'])
                if 'attached' in dfilter and dfilter['attached'] is not None:
                    attached = 'AND cs.server_id IS NOT NULL' if dfilter['attached'] == 'attached' else 'AND cs.server_id IS NULL'

            if dsort is not None:
                sort_column = dsort['column']
                sort_order = 'DESC' if dsort['desc'] else 'ASC'

            query = """
                SELECT CONCAT(available.user_id, '|', available.server_id) AS 'id', available.user_id, available.user, available.server_id, available.server, available.shared, cs.server_id IS NOT NULL AS 'attached', cs.date, cf.name AS 'folder'
                FROM (
                    SELECT u.id AS 'user_id', u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared
                    FROM servers s
                    JOIN groups g ON g.id = s.group_id
                    LEFT JOIN users u ON u.group_id = g.id
                    WHERE (s.shared = 1 OR u.id IS NOT NULL)
                    AND s.usage LIKE '%%C%%'
                    {} {}
                ) available
                LEFT JOIN client_servers cs USING (user_id, server_id)
                LEFT JOIN client_folders cf ON cf.id = cs.folder_id
                WHERE available.user_id IS NOT NULL {}
                ORDER BY {} {}
                LIMIT 1000
            """.format(user, server, attached, sort_column, sort_order)
            return self._sql.execute(query, args)

    def attach_servers(self, data):
        for server in data['servers']:
            query = """
                INSERT INTO client_servers (`user_id`, `server_id`, `date`)
                VALUES (%s, %s, %s)
            """
            self._sql.execute(query, (server['user_id'], server['server_id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def detach_servers(self, data):
        for server in data:
            query = """
                DELETE FROM client_servers
                WHERE user_id = %s
                AND server_id = %s
            """
            self._sql.execute(query, (server['user_id'], server['server_id']))