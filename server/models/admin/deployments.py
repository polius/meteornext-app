class Deployments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, dfilter=None, dsort=None):
        user = name = release = mode = method = status = created_from = created_to = started_from = started_to = ended_from = ended_to = ''
        args = {}
        sort_column = 'e.id'
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
                user = 'AND u.username = %(user)s'
                args['user'] = dfilter['user']
            if 'name' in dfilter and len(dfilter['name']) > 0 and 'nameFilter' in dfilter and dfilter['nameFilter'] in matching:
                name = f"AND d.name {matching[dfilter['nameFilter']]['operator']} %(name)s"
                args['name'] = matching[dfilter['nameFilter']]['args'].format(dfilter['name'])
            if 'release' in dfilter and len(dfilter['release']) > 0 and 'releaseFilter' in dfilter and dfilter['releaseFilter'] in matching:
                release = f"AND r.name {matching[dfilter['releaseFilter']]['operator']} %(release)s"
                args['release'] = matching[dfilter['releaseFilter']]['args'].format(dfilter['release'])
            if 'mode' in dfilter and dfilter['mode'] is not None and len(dfilter['mode']) > 0:
                mode = 'AND e.mode IN (%s)' % ','.join([f"%(mode{i})s" for i in range(len(dfilter['mode']))])
                for i,v in enumerate(dfilter['mode']):
                    args[f'mode{i}'] = v
            if 'method' in dfilter and dfilter['method'] is not None and len(dfilter['method']) > 0:
                method = 'AND e.method IN (%s)' % ','.join([f"%(method{i})s" for i in range(len(dfilter['method']))])
                for i,v in enumerate(dfilter['method']):
                    args[f'method{i}'] = v
            if 'status' in dfilter and dfilter['status'] is not None and len(dfilter['status']) > 0:
                status = 'AND e.status IN (%s)' % ','.join([f"%(status{i})s" for i in range(len(dfilter['status']))])
                for i,v in enumerate(dfilter['status']):
                    args[f'status{i}'] = v
            if 'createdFrom' in dfilter and len(dfilter['createdFrom']) > 0:
                created_from = 'AND e.created >= %(created_from)s'
                args['created_from'] = dfilter['createdFrom']
            if 'createdTo' in dfilter and len(dfilter['createdTo']) > 0:
                created_to = 'AND e.created <= %(created_to)s'
                args['created_to'] = dfilter['createdTo']
            if 'startedFrom' in dfilter and len(dfilter['startedFrom']) > 0:
                started_from = 'AND e.started >= %(started_from)s'
                args['started_from'] = dfilter['startedFrom']
            if 'startedTo' in dfilter and len(dfilter['startedTo']) > 0:
                started_to = 'AND e.started <= %(started_to)s'
                args['started_to'] = dfilter['startedTo']
            if 'endedFrom' in dfilter and len(dfilter['endedFrom']) > 0:
                ended_from = 'AND e.ended >= %(ended_from)s'
                args['ended_from'] = dfilter['endedFrom']
            if 'endedTo' in dfilter and len(dfilter['endedTo']) > 0:
                ended_to = 'AND e.ended <= %(ended_to)s'
                args['ended_to'] = dfilter['endedTo']

        if dsort is not None:
            sort_column = dsort['column']
            sort_order = 'DESC' if dsort['desc'] else 'ASC'

        query = """
                SELECT d.id, e.id AS 'execution_id', d.name, env.name AS 'environment', r.name AS 'release', u.id AS 'user_id', u.username, e.mode, e.method, e.status, q.queue, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall'
                FROM executions e
                JOIN deployments d ON d.id = e.deployment_id
                JOIN users u ON u.id = d.user_id {0}
                JOIN groups g ON g.id = u.group_id
                LEFT JOIN environments env ON env.id = e.environment_id
                LEFT JOIN releases r ON r.id = d.release_id
                LEFT JOIN
                (
                    SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                    FROM executions
                    JOIN (SELECT @cnt := 0) t
                    WHERE status = 'QUEUED'
                ) q ON q.deployment_id = d.id
                WHERE 1=1
                {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11}
                ORDER BY {12} {13}
                LIMIT 1000
        """.format(user, name, release, mode, method, status, created_from, created_to, started_from, started_to, ended_from, ended_to, sort_column, sort_order)
        return self._sql.execute(query, args)

    def get_users_list(self):
        query = """
            SELECT u.username AS 'user', g.name AS 'group'
            FROM users u
            JOIN groups g ON g.id = u.group_id
            ORDER BY u.username
        """
        return self._sql.execute(query)

    def put_name(self, user_id, deployment):
        query = """
            UPDATE deployments
            SET name = %s
            WHERE id = %s
            AND user_id = %s
        """
        self._sql.execute(query, (deployment['name'], deployment['id'], user_id))

    def put_release(self, user_id, deployment):
        query = """
            UPDATE deployments, releases
            SET deployments.release_id = releases.id
            WHERE deployments.id = %s
            AND deployments.user_id = %s
            AND releases.name = %s
            AND releases.user_id = %s
        """
        self._sql.execute(query, (deployment['id'], user_id, deployment['release'], user_id))