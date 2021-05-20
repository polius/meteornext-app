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
                    'equal': '= %s',
                    'not_equal': '!= %s',
                    'starts': "LIKE '%s%%'",
                    'not_starts': "NOT LIKE '%s%%",
                    'contains': "LIKE '%%%s%%'",
                    'not_contains': "NOT LIKE '%%%s%%",
                }
                if 'user' in dfilter and len(dfilter['user']) > 0:
                    user = 'AND u.username = %s'
                    args.append(dfilter['user'])
                if 'server' in dfilter and len(dfilter['server']) > 0:
                    server = 'AND s.name = %s'
                    args.append(dfilter['server'])
                if 'database' in dfilter and len(dfilter['database']) > 0 and 'databaseFilter' in dfilter and dfilter['databaseFilter'] in matching:
                    database = f"AND cq.database {dfilter['databaseFilter']}"
                    args.append(dfilter['database'])
                if 'query' in dfilter and len(dfilter['query']) > 0 and 'queryFilter' in dfilter and dfilter['queryFilter'] in matching:
                    database = f"AND cq.query {dfilter['queryFilter']}"
                    args.append(dfilter['query'])
                if 'status' in dfilter and len(dfilter['status']) > 0:
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

    def get_users(self):
        query = """
            SELECT u.username AS 'user', g.name AS 'group'
            FROM users u
            JOIN groups g ON g.id = u.group_id
            ORDER BY u.username
        """
        return self._sql.execute(query)

    def get_servers(self, dfilter=None, dsort=None):
        query = """
            SELECT CONCAT(available.user_id, '|', available.server_id) AS 'id', available.user_id, available.user_username, available.server_id, available.server_name, available.server_shared, cs.server_id IS NOT NULL AS 'server_attached', cs.date, cf.name AS 'folder_name'
            FROM (
                SELECT u.id AS 'user_id', u.username AS 'user_username', s.id AS 'server_id', s.name AS 'server_name', s.shared AS 'server_shared'
                FROM servers s
                JOIN groups g ON g.id = s.group_id
                LEFT JOIN users u ON u.group_id = g.id
                WHERE (s.shared = 1 OR u.id IS NOT NULL)
                AND s.usage LIKE '%C%'
            ) available
            LEFT JOIN client_servers cs USING (user_id, server_id)
            LEFT JOIN client_folders cf ON cf.id = cs.folder_id
            WHERE available.user_id IS NOT NULL
            ORDER BY cs.date DESC
            LIMIT 1000
        """
        return self._sql.execute(query)
