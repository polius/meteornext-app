class Restore:
    def __init__(self, sql):
        self._sql = sql

    def get(self, rfilter=None, rsort=None):
        user = mode = size = server = database = status = started_from = started_to = ended_from = ended_to = ''
        deleted = 'AND r.deleted = 0'
        args = {}
        sort_column = 'r.id'
        sort_order = 'DESC'
        if rfilter is not None:
            matching = {
                'equal':         { 'operator': '=', 'args': '{}' },
                'not_equal':     { 'operator': '!=', 'args': '{}' },
                'starts':        { 'operator': 'LIKE', 'args': '{}%' },
                'not_starts':    { 'operator': 'NOT LIKE', 'args': '{}%' },
                'contains':      { 'operator': 'LIKE', 'args': '%{}%' },
                'not_contains':  { 'operator': 'NOT LIKE', 'args': '%{}%' },
            }
            if 'user' in rfilter and rfilter['user'] is not None:
                user = 'AND u.username = %(user)s'
                args['user'] = rfilter['user']
            if 'mode' in rfilter and rfilter['mode'] is not None and len(rfilter['mode']) > 0:
                mode = 'AND r.mode IN (%s)' % ','.join([f"%(mode{i})s" for i in range(len(rfilter['mode']))])
                for i,v in enumerate(rfilter['mode']):
                    args[f'mode{i}'] = v
            if 'server' in rfilter and len(rfilter['server']) > 0 and 'serverFilter' in rfilter and rfilter['serverFilter'] in matching:
                server = f"AND s.name {matching[rfilter['serverFilter']]['operator']} %(server)s"
                args['server'] = matching[rfilter['serverFilter']]['args'].format(rfilter['server'])
            if 'database' in rfilter and len(rfilter['database']) > 0 and 'databaseFilter' in rfilter and rfilter['databaseFilter'] in matching:
                database = f"AND r.database {matching[rfilter['databaseFilter']]['operator']} %(database)s"
                args['database'] = matching[rfilter['databaseFilter']]['args'].format(rfilter['database'])
            if 'status' in rfilter and rfilter['status'] is not None and len(rfilter['status']) > 0:
                status = 'AND r.status IN (%s)' % ','.join([f"%(status{i})s" for i in range(len(rfilter['status']))])
                for i,v in enumerate(rfilter['status']):
                    args[f'status{i}'] = v
            if 'startedFrom' in rfilter and len(rfilter['startedFrom']) > 0:
                started_from = 'AND r.started >= %(started_from)s'
                args['started_from'] = rfilter['startedFrom']
            if 'startedTo' in rfilter and len(rfilter['startedTo']) > 0:
                started_to = 'AND r.started <= %(started_to)s'
                args['started_to'] = rfilter['startedTo']
            if 'endedFrom' in rfilter and len(rfilter['endedFrom']) > 0:
                ended_from = 'AND r.ended >= %(ended_from)s'
                args['ended_from'] = rfilter['endedFrom']
            if 'endedTo' in rfilter and len(rfilter['endedTo']) > 0:
                ended_to = 'AND r.ended <= %(ended_to)s'
                args['ended_to'] = rfilter['endedTo']
            if 'deleted' in rfilter and rfilter['deleted']:
                deleted = ''
                args['deleted'] = rfilter['deleted']

        if rsort is not None:
            sort_column = rsort['column']
            sort_order = 'DESC' if rsort['desc'] else 'ASC'

        query = """
                SELECT r.id, r.mode, r.source, r.size, r.server_id, s.name AS 'server', r.database, r.status, r.started, r.ended, r.user_id, u.username, r.deleted
                FROM restore r
                JOIN servers s ON s.id = r.server_id
                JOIN users u ON u.id = r.user_id
                WHERE 1=1
                {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10}
                ORDER BY {11} {12}
                LIMIT 1000
        """.format(user, mode, size, server, database, status, started_from, started_to, ended_from, ended_to, deleted, sort_column, sort_order)
        return self._sql.execute(query, args)

    def get_users_list(self):
        query = """
            SELECT u.username AS 'user', g.name AS 'group'
            FROM users u
            JOIN groups g ON g.id = u.group_id
            ORDER BY u.username
        """
        return self._sql.execute(query)

    def put(self, item, value):
        query = """
            UPDATE restore
            SET deleted = %s
            WHERE id = %s
        """
        self._sql.execute(query, (value, item))

    def delete(self, item):
        query = """
            DELETE FROM restore
            WHERE id = %s
        """
        self._sql.execute(query, (item))
