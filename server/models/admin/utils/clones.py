class Clones:
    def __init__(self, sql):
        self._sql = sql

    def get(self, efilter=None, esort=None):
        user = mode = size = source_server = source_database = destination_server = destination_database = status = created_from = created_to = started_from = started_to = ended_from = ended_to = ''
        deleted = 'AND c.deleted = 0'
        args = {}
        sort_column = 'c.id'
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
                mode = 'AND c.mode IN (%s)' % ','.join([f"%(mode{i})s" for i in range(len(efilter['mode']))])
                for i,v in enumerate(efilter['mode']):
                    args[f'mode{i}'] = v
            if 'sourceServer' in efilter and len(efilter['sourceServer']) > 0 and 'sourceServerFilter' in efilter and efilter['sourceServerFilter'] in matching:
                source_server = f"AND s.name {matching[efilter['sourceServerFilter']]['operator']} %(source_server)s"
                args['source_server'] = matching[efilter['sourceServerFilter']]['args'].format(efilter['sourceServer'])
            if 'sourceDatabase' in efilter and len(efilter['sourceDatabase']) > 0 and 'sourceDatabaseFilter' in efilter and efilter['sourceDatabaseFilter'] in matching:
                source_database = f"AND c.source_database {matching[efilter['sourceDatabaseFilter']]['operator']} %(source_database)s"
                args['source_database'] = matching[efilter['sourceDatabaseFilter']]['args'].format(efilter['sourceDatabase'])
            if 'destinationServer' in efilter and len(efilter['destinationServer']) > 0 and 'destinationServerFilter' in efilter and efilter['destinationServerFilter'] in matching:
                destination_server = f"AND s2.name {matching[efilter['destinationServerFilter']]['operator']} %(destination_server)s"
                args['destination_server'] = matching[efilter['destinationServerFilter']]['args'].format(efilter['destinationServer'])
            if 'destinationDatabase' in efilter and len(efilter['destinationDatabase']) > 0 and 'destinationDatabaseFilter' in efilter and efilter['destinationDatabaseFilter'] in matching:
                destination_database = f"AND c.destination_database {matching[efilter['destinationDatabaseFilter']]['operator']} %(destination_database)s"
                args['destination_database'] = matching[efilter['destinationDatabaseFilter']]['args'].format(efilter['destinationDatabase'])
            if 'status' in efilter and efilter['status'] is not None and len(efilter['status']) > 0:
                status = 'AND c.status IN (%s)' % ','.join([f"%(status{i})s" for i in range(len(efilter['status']))])
                for i,v in enumerate(efilter['status']):
                    args[f'status{i}'] = v
            if 'createdFrom' in efilter and len(efilter['createdFrom']) > 0:
                created_from = 'AND c.created >= %(created_from)s'
                args['created_from'] = efilter['createdFrom']
            if 'createdTo' in efilter and len(efilter['createdTo']) > 0:
                created_to = 'AND c.created <= %(created_to)s'
                args['created_to'] = efilter['createdTo']
            if 'startedFrom' in efilter and len(efilter['startedFrom']) > 0:
                started_from = 'AND c.started >= %(started_from)s'
                args['started_from'] = efilter['startedFrom']
            if 'startedTo' in efilter and len(efilter['startedTo']) > 0:
                started_to = 'AND c.started <= %(started_to)s'
                args['started_to'] = efilter['startedTo']
            if 'endedFrom' in efilter and len(efilter['endedFrom']) > 0:
                ended_from = 'AND c.ended >= %(ended_from)s'
                args['ended_from'] = efilter['endedFrom']
            if 'endedTo' in efilter and len(efilter['endedTo']) > 0:
                ended_to = 'AND c.ended <= %(ended_to)s'
                args['ended_to'] = efilter['endedTo']
            if 'deleted' in efilter and efilter['deleted']:
                deleted = ''
                args['deleted'] = efilter['deleted']

        if esort is not None and esort['column'] in ['user','mode','source_server_name','destination_server_name','source_database','destination_database','size','status','created','started','ended','overall','deleted']:
            sort_column = f"`{esort['column']}`"
            sort_order = 'DESC' if esort['desc'] == 'true' else 'ASC'

        query = """
            SELECT c.id, c.mode, c.source_server, c.source_database, c.destination_server, c.destination_database, c.size, c.uri, c.status, c.created, c.started, c.ended, c.deleted, s.name AS 'source_server_name', s.shared AS 'source_server_shared', s.secured AS 'source_server_secured', s2.name AS 'destination_server_name', s2.shared AS 'destination_server_shared', s2.secured AS 'destination_server_secured', CONCAT(TIMEDIFF(IF(c.status IN('IN PROGRESS','STOPPING'), UTC_TIMESTAMP(), c.ended), c.started)) AS 'overall', u.username, q.queue
            FROM clones c
            JOIN servers s ON s.id = c.source_server
            JOIN servers s2 ON s2.id = c.destination_server
            JOIN users u ON u.id = c.user_id
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
            WHERE 1=1
            {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} {12} {13} {14}
            ORDER BY {15} {16}
            LIMIT 1000
        """.format(user, mode, size, source_server, source_database, destination_server, destination_database, status, created_from, created_to, started_from, started_to, ended_from, ended_to, deleted, sort_column, sort_order)
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
            UPDATE clones
            SET deleted = %s
            WHERE id = %s
        """
        self._sql.execute(query, (value, item))

    def delete(self, item):
        query = """
            DELETE FROM clones
            WHERE id = %s
        """
        self._sql.execute(query, (item))
