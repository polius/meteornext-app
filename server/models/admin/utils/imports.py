class Imports:
    def __init__(self, sql):
        self._sql = sql

    def get(self, rfilter=None, rsort=None):
        user = mode = size = server = database = status = created_from = created_to = started_from = started_to = ended_from = ended_to = ''
        deleted = 'AND i.deleted = 0'
        args = {}
        sort_column = 'i.id'
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
                mode = 'AND i.mode IN (%s)' % ','.join([f"%(mode{i})s" for i in range(len(rfilter['mode']))])
                for i,v in enumerate(rfilter['mode']):
                    args[f'mode{i}'] = v
            if 'server' in rfilter and len(rfilter['server']) > 0 and 'serverFilter' in rfilter and rfilter['serverFilter'] in matching:
                server = f"AND s.name {matching[rfilter['serverFilter']]['operator']} %(server)s"
                args['server'] = matching[rfilter['serverFilter']]['args'].format(rfilter['server'])
            if 'database' in rfilter and len(rfilter['database']) > 0 and 'databaseFilter' in rfilter and rfilter['databaseFilter'] in matching:
                database = f"AND i.database {matching[rfilter['databaseFilter']]['operator']} %(database)s"
                args['database'] = matching[rfilter['databaseFilter']]['args'].format(rfilter['database'])
            if 'status' in rfilter and rfilter['status'] is not None and len(rfilter['status']) > 0:
                status = 'AND i.status IN (%s)' % ','.join([f"%(status{i})s" for i in range(len(rfilter['status']))])
                for i,v in enumerate(rfilter['status']):
                    args[f'status{i}'] = v
            if 'createdFrom' in rfilter and len(rfilter['createdFrom']) > 0:
                created_from = 'AND i.created >= %(created_from)s'
                args['created_from'] = rfilter['createdFrom']
            if 'createdTo' in rfilter and len(rfilter['createdTo']) > 0:
                created_to = 'AND i.created <= %(created_to)s'
                args['created_to'] = rfilter['createdTo']
            if 'startedFrom' in rfilter and len(rfilter['startedFrom']) > 0:
                started_from = 'AND i.started >= %(started_from)s'
                args['started_from'] = rfilter['startedFrom']
            if 'startedTo' in rfilter and len(rfilter['startedTo']) > 0:
                started_to = 'AND i.started <= %(started_to)s'
                args['started_to'] = rfilter['startedTo']
            if 'endedFrom' in rfilter and len(rfilter['endedFrom']) > 0:
                ended_from = 'AND i.ended >= %(ended_from)s'
                args['ended_from'] = rfilter['endedFrom']
            if 'endedTo' in rfilter and len(rfilter['endedTo']) > 0:
                ended_to = 'AND i.ended <= %(ended_to)s'
                args['ended_to'] = rfilter['endedTo']
            if 'deleted' in rfilter and rfilter['deleted']:
                deleted = ''
                args['deleted'] = rfilter['deleted']

        if rsort is not None and rsort['column'] in ['user','mode','server_name','database','size','status','created','started','ended','overall','deleted']:
            sort_column = f"`{rsort['column']}`"
            sort_order = 'DESC' if rsort['desc'] == 'true' else 'ASC'

        query = """
                SELECT i.id, i.mode, i.source, i.size, i.server_id, s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', i.database, i.uri, i.status, i.created, i.started, i.ended, CONCAT(TIMEDIFF(IF(i.status IN('IN PROGRESS','STOPPING'), UTC_TIMESTAMP(), i.ended), i.started)) AS 'overall', i.user_id, u.username, i.deleted, q.queue
                FROM imports i
                JOIN servers s ON s.id = i.server_id
                JOIN users u ON u.id = i.user_id
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
                ) q ON q.source_id = i.id AND q.source_type = 'import'
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
            UPDATE imports
            SET deleted = %s
            WHERE id = %s
        """
        self._sql.execute(query, (value, item))

    def delete(self, item):
        query = """
            DELETE FROM imports
            WHERE id = %s
        """
        self._sql.execute(query, (item))
