class Deployments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id=None, deployment_id=None, dfilter=None, dsort=None):
        if deployment_id is not None:
            query = """
                SELECT d.id, e.id AS 'execution_id', e.uri, d.name, env.name AS 'environment', r.name AS 'release', e.mode, e.method, e.status, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall'
                FROM executions e
                JOIN deployments d ON d.id = e.deployment_id AND d.user_id = %(user_id)s AND d.id = %(deployment_id)s
                JOIN users u ON u.id = d.user_id
                JOIN groups g ON g.id = u.group_id
                LEFT JOIN environments env ON env.id = e.environment_id
                LEFT JOIN releases r ON r.id = d.release_id 
                WHERE e.id IN (
                    SELECT MAX(id)
                    FROM executions e2
                    WHERE e2.deployment_id = e.deployment_id
                )
                AND (r.active = 1 OR r.active IS NULL)
                ORDER BY id DESC
            """
            return self._sql.execute(query, {'user_id': user_id, 'deployment_id': deployment_id})
        else:
            name = release = mode = method = status = created_from = created_to = started_from = started_to = ended_from = ended_to = ''
            all_executions = 'AND e.id IN (SELECT MAX(id) FROM executions e2 WHERE e2.deployment_id = e.deployment_id)'
            active_release = 'AND (r.active = 1 OR r.active IS NULL)'
            args = { 'user_id': user_id }
            if dfilter is not None:
                active_release = ''
                if 'name' in dfilter and len(dfilter['name']) > 0:
                    name = "AND d.name = %(name)s"
                    args['name'] = dfilter['name']
                if 'release' in dfilter and len(dfilter['release']) > 0:
                    release = "AND r.name = %(release)s"
                    args['release'] = dfilter['release']
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
                if 'allExecutions' in dfilter and dfilter['allExecutions']:
                    all_executions = ''

            query = """
                SELECT d.id, e.id AS 'execution_id', e.uri, d.name, env.name AS 'environment', r.name AS 'release', e.mode, e.method, e.status, q.queue, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall'
                FROM executions e
                JOIN deployments d ON d.id = e.deployment_id AND d.user_id = %(user_id)s
                JOIN users u ON u.id = d.user_id
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
                {0}
                {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11}
                {12}
                ORDER BY created DESC, id DESC
            """.format(active_release, name, release, mode, method, status, created_from, created_to, started_from, started_to, ended_from, ended_to, all_executions)
        return self._sql.execute(query, args)

    def post(self, user_id, deployment):
        query = """
            INSERT INTO deployments (name, release_id, user_id)
            SELECT %(name)s, id, %(user_id)s
            FROM releases
            WHERE name = %(release_id)s
            AND user_id = %(user_id)s
        """
        return self._sql.execute(query, {'name': deployment['name'], 'user_id': user_id, 'release_id': deployment['release_id']})

    def putName(self, user, deployment):
        query = """
            UPDATE deployments
            SET name = %s
            WHERE id = %s
            AND user_id = %s
        """
        self._sql.execute(query, (deployment['name'], deployment['id'], user['id']))

    def putRelease(self, user, deployment):
        query = """
            UPDATE deployments, releases
            SET deployments.release_id = releases.id
            WHERE deployments.id = %s
            AND deployments.user_id = %s
            AND releases.name = %s
            AND releases.user_id = %s
        """
        self._sql.execute(query, (deployment['id'], user['id'], deployment['release'], user['id']))

    def getResults(self, uri):
        query = """
            SELECT d.user_id, e.deployment_id, e.id AS 'execution_id', e.mode, e.logs, e.shared
            FROM executions e
            JOIN deployments d ON d.id = e.deployment_id
            WHERE e.uri = %(uri)s
        """
        return self._sql.execute(query, {'uri': uri})

    def getUser(self, deployment_id):
        query = """
            SELECT u.id, u.group_id
            FROM deployments d
            JOIN users u ON u.id = d.user_id
            WHERE d.id = %s
        """
        return self._sql.execute(query, (deployment_id))

    def getExecutions(self, deployment_id):
        query = """
            SELECT e.id, e.uri, env.name AS 'environment', e.mode, e.method, e.status, q.queue, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall'
            FROM executions e
            JOIN deployments d ON d.id = e.deployment_id AND d.id = %(deployment_id)s
            LEFT JOIN environments env ON env.id = e.environment_id
            LEFT JOIN
            (
                SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                FROM executions
                JOIN (SELECT @cnt := 0) t
                WHERE status = 'QUEUED'
            ) q ON q.deployment_id = d.id
            ORDER BY e.created DESC
        """
        return self._sql.execute(query, {'deployment_id': deployment_id})

    def getDeploymentsName(self, user_id):
        query = """
            SELECT DISTINCT(name) AS 'name'
            FROM executions e
            JOIN deployments d ON d.id = e.deployment_id AND d.user_id = %s
            ORDER BY name
        """
        return self._sql.execute(query, (user_id))

    def removeRelease(self, release_id):
        query = """
            UPDATE deployments 
            SET release_id = NULL 
            WHERE release_id = %s
        """
        return self._sql.execute(query, (release_id))
