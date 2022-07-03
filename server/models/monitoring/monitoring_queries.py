class Monitoring_Queries:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def get(self, user, mfilter=None, msort=None):
        server = host = user_text = database = query_text = first_seen_from = first_seen_to = last_seen_from = last_seen_to = ''
        args = {}
        sort_column = 'q.last_seen'
        sort_order = 'DESC'
        if mfilter is not None:
            matching = {
                'equal':        { 'operator': '=', 'args': '{}' },
                'not_equal':    { 'operator': '!=', 'args': '{}' },
                'starts':       { 'operator': 'LIKE', 'args': '{}%' },
                'not_starts':   { 'operator': 'NOT LIKE', 'args': '{}%' },
                'contains':     { 'operator': 'LIKE', 'args': '%{}%' },
                'not_contains': { 'operator': 'NOT LIKE', 'args': '%{}%' }
            }
            if 'server' in mfilter and mfilter['server'] is not None:
                server = 'AND q.server_id = %(server)s'
                args['server'] = mfilter['server']
            if 'host' in mfilter and len(mfilter['host']) > 0 and 'hostFilter' in mfilter and mfilter['hostFilter'] in matching:
                host = f"AND q.host {matching[mfilter['hostFilter']]['operator']} %(host)s"
                args['host'] = matching[mfilter['hostFilter']]['args'].format(mfilter['host'])
            if 'user' in mfilter and len(mfilter['user']) > 0 and 'userFilter' in mfilter and mfilter['userFilter'] in matching:
                user_text = f"AND q.user {matching[mfilter['userFilter']]['operator']} %(user)s"
                args['user'] = matching[mfilter['userFilter']]['args'].format(mfilter['user'])
            if 'database' in mfilter and len(mfilter['database']) > 0 and 'databaseFilter' in mfilter and mfilter['databaseFilter'] in matching:
                database = f"AND q.db {matching[mfilter['databaseFilter']]['operator']} %(database)s"
                args['database'] = matching[mfilter['databaseFilter']]['args'].format(mfilter['database'])
            if 'query' in mfilter and len(mfilter['query']) > 0 and 'queryFilter' in mfilter and mfilter['queryFilter'] in matching:
                query_text = f"AND q.query_text {matching[mfilter['queryFilter']]['operator']} %(query)s"
                args['query'] = matching[mfilter['queryFilter']]['args'].format(mfilter['query'])
            if 'firstSeenFrom' in mfilter and len(mfilter['firstSeenFrom']) > 0:
                first_seen_from = 'AND q.first_seen >= %(first_seen_from)s'
                args['first_seen_from'] = mfilter['firstSeenFrom']
            if 'firstSeenTo' in mfilter and len(mfilter['firstSeenTo']) > 0:
                first_seen_to = 'AND q.first_seen <= %(first_seen_to)s'
                args['first_seen_to'] = mfilter['firstSeenTo']
            if 'lastSeenFrom' in mfilter and len(mfilter['lastSeenFrom']) > 0:
                last_seen_from = 'AND q.last_seen >= %(last_seen_from)s'
                args['last_seen_from'] = mfilter['lastSeenFrom']
            if 'lastSeenTo' in mfilter and len(mfilter['lastSeenTo']) > 0:
                last_seen_to = 'AND q.last_seen <= %(last_seen_to)s'
                args['last_seen_to'] = mfilter['lastSeenTo']

        if msort is not None:
            sort_column = 's.name' if msort['column'] == 'server' else f"q.{msort['column']}"
            sort_order = 'DESC' if msort['desc'] else 'ASC'

        query = """
            SELECT q.id, s.id AS 'server_id', s.name AS 'server', s.shared, s.secured, q.query_text, q.db, q.user, q.host, q.first_seen, q.last_seen, q.last_execution_time, q.max_execution_time, q.avg_execution_time, q.count
            FROM monitoring_queries q
            JOIN monitoring m ON m.server_id = q.server_id AND m.queries_enabled = 1 AND m.user_id = {0}
            JOIN servers s ON s.id = q.server_id
            JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = {1}
                AND (s.shared = 1 OR s.owner_id = {0})
                AND ({13} = -1 OR (@cnt := @cnt + 1) <= {13})
                ORDER BY s.id
            ) t ON t.id = s.id
            WHERE 1=1
            {2} {3} {4} {5} {6} {7} {8} {9} {10}
            ORDER BY {11} {12}
            LIMIT 1000
        """.format(user['id'], user['group_id'], server, host, user_text, database, query_text, first_seen_from, first_seen_to, last_seen_from, last_seen_to, sort_column, sort_order, self._license.get_resources())
        return self._sql.execute(query, args)
