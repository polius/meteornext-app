class Deployments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, dfilter=None, dsort=None):
        user = name = release = mode = status = date_from = date_to = ''
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
            if 'mode' in dfilter and dfilter['mode'] is not None:
                mode = 'AND e.mode = %(mode)s'
                args['mode'] = dfilter['mode']
            if 'status' in dfilter and dfilter['status'] is not None:
                status = 'AND e.status = %(status)s'
                args['status'] = dfilter['status']
            if 'dateFrom' in dfilter and len(dfilter['dateFrom']) > 0:
                date_from = 'AND e.created >= %(date_from)s'
                args['date_from'] = dfilter['dateFrom']
            if 'dateTo' in dfilter and len(dfilter['dateTo']) > 0:
                date_to = 'AND e.created <= %(date_to)s'
                args['date_to'] = dfilter['dateTo']

        if dsort is not None:
            sort_column = dsort['column']
            sort_order = 'DESC' if dsort['desc'] else 'ASC'

        query = """
                SELECT d.id, e.id AS 'execution_id', d.name, env.name AS 'environment', r.name AS 'release', u.username, e.mode, e.method, e.status, q.queue, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall'
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
                WHERE e.id IN (
                    SELECT MAX(id)
                    FROM executions e2
                    WHERE e2.deployment_id = e.deployment_id
                )
                {1} {2} {3} {4} {5} {6}
                ORDER BY {7} {8}
                LIMIT 1000
        """.format(user, name, release, mode, status, date_from, date_to, sort_column, sort_order)
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