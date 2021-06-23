class Deployments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id=None, deployment_id=None):
        if deployment_id is not None:
            query = """
                SELECT d.id, e.id AS 'execution_id', d.name, env.name AS 'environment', r.name AS 'release', e.mode, e.method, e.status, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall'
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
            query = """
                SELECT d.id, e.id AS 'execution_id', d.name, env.name AS 'environment', r.name AS 'release', e.mode, e.method, e.status, q.queue, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall'
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
                WHERE e.id IN (
                    SELECT MAX(id)
                    FROM executions e2
                    WHERE e2.deployment_id = e.deployment_id
                )
                AND (r.active = 1 OR r.active IS NULL)
                ORDER BY created DESC, id DESC
            """
            return self._sql.execute(query, {"user_id": user_id})

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
            SELECT d.user_id, e.deployment_id, e.id AS 'execution_id', e.mode, engine, public
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
            SELECT e.id, env.name AS 'environment', e.mode, e.method, e.status, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall'
            FROM executions e
            LEFT JOIN environments env ON env.id = e.environment_id
            WHERE e.deployment_id = %(deployment_id)s
            ORDER BY e.created DESC
        """
        return self._sql.execute(query, {'deployment_id': deployment_id})

    def removeRelease(self, release_id):
        query = """
            UPDATE deployments 
            SET release_id = NULL 
            WHERE release_id = %s
        """
        return self._sql.execute(query, (release_id))
