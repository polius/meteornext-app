class Clones:
    def __init__(self, sql):
        self._sql = sql

    def get(self, efilter=None, esort=None):
        user = mode = size = origin_server = origin_database = destination_server = destination_database = status = started_from = started_to = ended_from = ended_to = ''
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
            if 'originServer' in efilter and len(efilter['originServer']) > 0 and 'originServerFilter' in efilter and efilter['originServerFilter'] in matching:
                origin_server = f"AND s.name {matching[efilter['originServerFilter']]['operator']} %(origin_server)s"
                args['origin_server'] = matching[efilter['originServerFilter']]['args'].format(efilter['origin_server'])
            if 'originDatabase' in efilter and len(efilter['originDatabase']) > 0 and 'originDatabaseFilter' in efilter and efilter['originDatabaseFilter'] in matching:
                origin_database = f"AND c.origin_database {matching[efilter['originDatabaseFilter']]['operator']} %(origin_database)s"
                args['origin_database'] = matching[efilter['originDatabaseFilter']]['args'].format(efilter['origin_database'])
            if 'destinationServer' in efilter and len(efilter['destinationServer']) > 0 and 'destinationServerFilter' in efilter and efilter['destinationServerFilter'] in matching:
                destination_server = f"AND s2.name {matching[efilter['destinationServerFilter']]['operator']} %(destination_server)s"
                args['destination_server'] = matching[efilter['destinationServerFilter']]['args'].format(efilter['destination_server'])
            if 'destinationDatabase' in efilter and len(efilter['destinationDatabase']) > 0 and 'destinationDatabaseFilter' in efilter and efilter['destinationDatabaseFilter'] in matching:
                destination_database = f"AND c.destination_database {matching[efilter['destinationDatabaseFilter']]['operator']} %(destination_database)s"
                args['destination_database'] = matching[efilter['destinationDatabaseFilter']]['args'].format(efilter['destination_database'])
            if 'status' in efilter and efilter['status'] is not None and len(efilter['status']) > 0:
                status = 'AND c.status IN (%s)' % ','.join([f"%(status{i})s" for i in range(len(efilter['status']))])
                for i,v in enumerate(efilter['status']):
                    args[f'status{i}'] = v
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

        if esort is not None:
            sort_column = f"`{esort['column']}`"
            sort_order = 'DESC' if esort['desc'] else 'ASC'

        query = """
                SELECT c.id, c.mode, c.origin_server, c.origin_database, c.destination_server, c.destination_database, c.size, c.uri, c.status, c.started, c.ended, c.deleted, s.name AS 'origin_server_name', s2.name AS 'destination_server_name', CONCAT(TIMEDIFF(c.ended, c.started)) AS 'overall', u.username
                FROM clones c
                JOIN servers s ON s.id = c.origin_server
                JOIN servers s2 ON s.id = c.destination_server
                JOIN users u ON u.id = c.user_id
                WHERE 1=1
                {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} {12}
                ORDER BY {13} {14}
                LIMIT 1000
        """.format(user, mode, size, origin_server, origin_database, destination_server, destination_database, status, started_from, started_to, ended_from, ended_to, deleted, sort_column, sort_order)
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
