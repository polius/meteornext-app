from datetime import datetime

class Client:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def get_queries(self, dfilter=None, dsort=None):
        if dfilter is None and dsort is None:
            query = """
                SELECT cq.id, u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared, s.secured, cq.database, cq.query, cq.status, cq.start_date, cq.end_date, cq.records, cq.elapsed, cq.error
                FROM client_queries cq
                JOIN users u ON u.id = cq.user_id
                JOIN servers s ON s.id = cq.server_id
                ORDER BY cq.id DESC
                LIMIT 1000
            """
            return self._sql.execute(query)
        else:
            user = server = database = query = status = start_date_from = start_date_to = end_date_from = end_date_to = ''
            args = []
            sort_column = 'cq.id'
            sort_order = 'DESC'
            if dfilter is not None:
                matching = {
                    'equal':        { 'operator': '=', 'args': '{}' },
                    'not_equal':    { 'operator': '!=', 'args': '{}' },
                    'starts':       { 'operator': 'LIKE', 'args': '{}%' },
                    'not_starts':   { 'operator': 'NOT LIKE', 'args': '{}%' },
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
                if 'status' in dfilter and dfilter['status'] is not None and len(dfilter['status']) > 0:
                    status = 'AND e.status IN (%s)' % ','.join([f"%(status{i})s" for i in range(len(dfilter['status']))])
                    for i,v in enumerate(dfilter['status']):
                        args[f'status{i}'] = v
                if 'startDateFrom' in dfilter and len(dfilter['startDateFrom']) > 0:
                    start_date_from = 'AND cq.start_date >= %s'
                    args.append(dfilter['startDateFrom'])
                if 'startDateTo' in dfilter and len(dfilter['startDateTo']) > 0:
                    start_date_to = 'AND cq.start_date <= %s'
                    args.append(dfilter['startDateTo'])
                if 'endDateFrom' in dfilter and len(dfilter['endDateFrom']) > 0:
                    start_date_from = 'AND cq.end_date >= %s'
                    args.append(dfilter['endDateFrom'])
                if 'endDateTo' in dfilter and len(dfilter['endDateTo']) > 0:
                    start_date_to = 'AND cq.end_date <= %s'
                    args.append(dfilter['endDateTo'])

            if dsort is not None and dsort['column'] in ['start_date','end_date','elapsed','user','server','database','status','records']:
                sort_column = f"`{dsort['column']}`"
                sort_order = 'DESC' if dsort['desc'] else 'ASC'

            query = """
                SELECT cq.id, u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared, s.secured, cq.database, cq.query, cq.status, cq.start_date, cq.end_date, cq.records, cq.elapsed, cq.error
                FROM client_queries cq
                JOIN users u ON u.id = cq.user_id
                JOIN servers s ON s.id = cq.server_id
                WHERE 1=1
                {} {} {} {} {} {} {} {} {}
                ORDER BY {} {}
                LIMIT 1000
            """.format(user, server, database, query, status, start_date_from, start_date_to, end_date_from, end_date_to, sort_column, sort_order)
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
                SELECT CONCAT(available.user_id, '|', available.server_id) AS 'id', available.user_id, available.user, available.server_id, available.server, t.active, available.shared, available.secured, cs.server_id IS NOT NULL AS 'attached', cs.date, cf.name AS 'folder'
                FROM (
                    SELECT u.id AS 'user_id', u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared, s.secured
                    FROM servers s
                    JOIN groups g ON g.id = s.group_id
                    LEFT JOIN users u ON u.group_id = g.id
                    WHERE (s.shared = 1 OR s.owner_id = u.id)
                    AND s.usage LIKE '%%C%%'
                ) available
                LEFT JOIN client_servers cs USING (user_id, server_id)
                LEFT JOIN client_folders cf ON cf.id = cs.folder_id
                JOIN (
                    SELECT
                        u.id AS 'user_id',
                        s.id AS 'server_id',
                        IF(@usr != u.id, @cnt := 0, @cnt := @cnt) AS 'logic1',
                        IF(%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s, 1, 0) AS 'active',
                        @usr := u.id AS 'logic2'
                    FROM users u
                    JOIN (SELECT @cnt := 0, @usr := 0) t
                    JOIN servers s ON s.group_id = u.group_id AND (s.shared = 1 OR s.owner_id = u.id)
                    ORDER BY u.id, s.id
                ) t ON t.user_id = u.available.user_id AND t.server_id = available.server_id
                WHERE available.user_id IS NOT NULL
                ORDER BY cs.date DESC, available.user ASC, available.server ASC
                LIMIT 1000
            """
            return self._sql.execute(query, {"license": self._license.get_resources()})
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
            args.append(self._license.get_resources())
            args.append(self._license.get_resources())
            if dfilter is not None:
                if 'attached' in dfilter and dfilter['attached'] is not None:
                    attached = 'AND cs.server_id IS NOT NULL' if dfilter['attached'] == 'attached' else 'AND cs.server_id IS NULL'

            if dsort is not None and dsort['column'] in ['user','server','attached','date','folder']:
                sort_column = f"`{dsort['column']}`"
                sort_order = 'DESC' if dsort['desc'] else 'ASC'

            query = """
                SELECT CONCAT(available.user_id, '|', available.server_id) AS 'id', available.user_id, available.user, available.server_id, available.server, t.active, available.shared, available.secured, cs.server_id IS NOT NULL AS 'attached', cs.date, cf.name AS 'folder'
                FROM (
                    SELECT u.id AS 'user_id', u.username AS 'user', s.id AS 'server_id', s.name AS 'server', s.shared, s.secured
                    FROM servers s
                    JOIN groups g ON g.id = s.group_id
                    LEFT JOIN users u ON u.group_id = g.id
                    WHERE (s.shared = 1 OR s.owner_id = u.id)
                    AND s.usage LIKE '%%C%%'
                    {} {}
                ) available
                LEFT JOIN client_servers cs USING (user_id, server_id)
                LEFT JOIN client_folders cf ON cf.id = cs.folder_id
                JOIN (
                    SELECT
                        u.id AS 'user_id',
                        s.id AS 'server_id',
                        IF(@usr != u.id, @cnt := 0, @cnt := @cnt) AS 'logic1',
                        IF(%s = -1 OR (@cnt := @cnt + 1) <= %s, 1, 0) AS 'active',
                        @usr := u.id AS 'logic2'
                    FROM users u
                    JOIN (SELECT @cnt := 0, @usr := 0) t
                    JOIN servers s ON s.group_id = u.group_id AND (s.shared = 1 OR s.owner_id = u.id)
                    ORDER BY u.id, s.id
                ) t ON t.user_id = u.available.user_id AND t.server_id = available.server_id
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
