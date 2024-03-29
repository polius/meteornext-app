class Exports:
    def __init__(self, sql):
        self._sql = sql

    def get(self, efilter=None, esort=None):
        user = mode = size = server = database = status = created_from = created_to = started_from = started_to = ended_from = ended_to = ''
        deleted = 'AND e.deleted = 0'
        args = {}
        sort_column = 'e.id'
        sort_order = 'DESC'
        if efilter is not None:
            matching = {
                'equal':         { 'operator': '=', 'args': '{}' },
                'not_equal':     { 'operator': '!=', 'args': '{}' },
                'starts':        { 'operator': 'LIKE', 'args': '{}%' },
                'not_starts':    { 'operator': 'NOT LIKE', 'args': '{}%' },
                'contains':      { 'operator': 'LIKE', 'args': '%{}%' },
                'not_contains':  { 'operator': 'NOT LIKE', 'args': '%{}%' },
            }
            if 'user' in efilter and efilter['user'] is not None:
                user = 'AND u.username = %(user)s'
                args['user'] = efilter['user']
            if 'mode' in efilter and efilter['mode'] is not None and len(efilter['mode']) > 0:
                mode = 'AND e.mode IN (%s)' % ','.join([f"%(mode{i})s" for i in range(len(efilter['mode']))])
                for i,v in enumerate(efilter['mode']):
                    args[f'mode{i}'] = v
            if 'server' in efilter and len(efilter['server']) > 0 and 'serverFilter' in efilter and efilter['serverFilter'] in matching:
                server = f"AND s.name {matching[efilter['serverFilter']]['operator']} %(server)s"
                args['server'] = matching[efilter['serverFilter']]['args'].format(efilter['server'])
            if 'database' in efilter and len(efilter['database']) > 0 and 'databaseFilter' in efilter and efilter['databaseFilter'] in matching:
                database = f"AND e.database {matching[efilter['databaseFilter']]['operator']} %(database)s"
                args['database'] = matching[efilter['databaseFilter']]['args'].format(efilter['database'])
            if 'status' in efilter and efilter['status'] is not None and len(efilter['status']) > 0:
                status = 'AND e.status IN (%s)' % ','.join([f"%(status{i})s" for i in range(len(efilter['status']))])
                for i,v in enumerate(efilter['status']):
                    args[f'status{i}'] = v
            if 'createdFrom' in efilter and len(efilter['createdFrom']) > 0:
                created_from = 'AND e.created >= %(created_from)s'
                args['created_from'] = efilter['createdFrom']
            if 'createdTo' in efilter and len(efilter['createdTo']) > 0:
                created_to = 'AND e.created <= %(created_to)s'
                args['created_to'] = efilter['createdTo']
            if 'startedFrom' in efilter and len(efilter['startedFrom']) > 0:
                started_from = 'AND e.started >= %(started_from)s'
                args['started_from'] = efilter['startedFrom']
            if 'startedTo' in efilter and len(efilter['startedTo']) > 0:
                started_to = 'AND e.started <= %(started_to)s'
                args['started_to'] = efilter['startedTo']
            if 'endedFrom' in efilter and len(efilter['endedFrom']) > 0:
                ended_from = 'AND e.ended >= %(ended_from)s'
                args['ended_from'] = efilter['endedFrom']
            if 'endedTo' in efilter and len(efilter['endedTo']) > 0:
                ended_to = 'AND e.ended <= %(ended_to)s'
                args['ended_to'] = efilter['endedTo']
            if 'deleted' in efilter and efilter['deleted']:
                deleted = ''
                args['deleted'] = efilter['deleted']

        if esort is not None and esort['column'] in ['user','mode','server_name','database','size','status','created','started','ended','overall','deleted']:
            sort_column = f"`{esort['column']}`"
            sort_order = 'DESC' if esort['desc'] == 'true' else 'ASC'

        query = """
            SELECT e.id, e.mode, e.server_id, e.database, e.size, e.uri, e.status, e.created, e.started, e.ended, e.deleted, s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', CONCAT(TIMEDIFF(IF(e.status IN('IN PROGRESS','STOPPING'), UTC_TIMESTAMP(), e.ended), e.started)) AS 'overall', u.username, q.queue
            FROM exports e
            JOIN servers s ON s.id = e.server_id
            JOIN users u ON u.id = e.user_id
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
            WHERE 1=1
            {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} {12}
            ORDER BY {13} {14}
            LIMIT 1000
        """.format(user, mode, size, server, database, status, created_from, created_to, started_from, started_to, ended_from, ended_to, deleted, sort_column, sort_order)
        return self._sql.execute(query, args)

    def get_users_list(self):
        query = """
            SELECT u.username AS 'user', g.name AS 'group'
            FROM users u
            JOIN `groups` g ON g.id = u.group_id
            ORDER BY u.username
        """
        return self._sql.execute(query)

    def put(self, item, value):
        query = """
            UPDATE exports
            SET deleted = %s
            WHERE id = %s
        """
        self._sql.execute(query, (value, item))

    def delete(self, item):
        query = """
            DELETE FROM exports
            WHERE id = %s
        """
        self._sql.execute(query, (item))
