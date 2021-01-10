from datetime import datetime

class Deployments_Basic:
    def __init__(self, sql):
        self._sql = sql

    def get(self, execution_id):
        query = """
            SELECT d.id, b.id AS 'execution_id', 'BASIC' AS 'mode', d.name, r.name AS 'release', e.name AS 'environment', b.databases, b.queries, b.method, b.status, b.stopped, q.queue, b.created, b.scheduled, b.started, b.ended, CONCAT(TIMEDIFF(b.ended, b.started)) AS 'overall', b.error, b.progress, b.url, b.uri, b.engine, b.public
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id
            LEFT JOIN releases r ON r.id = d.release_id
            LEFT JOIN environments e ON e.id = b.environment_id
            LEFT JOIN
            (
                SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                FROM deployments_basic
                JOIN (SELECT @cnt := 0) t
                WHERE status = 'QUEUED'
            ) q ON q.deployment_id = d.id
            WHERE b.id = %s
        """
        return self._sql.execute(query, (execution_id))

    def post(self, deployment):
        query = """
            INSERT INTO deployments_basic (deployment_id, environment_id, `databases`, queries, method, `status`, created, scheduled, url)
            SELECT %s, e.id, %s, %s, %s, %s, %s, IF(%s = '', NULL, %s), %s
            FROM environments e
            WHERE e.name = %s
            AND e.group_id = %s
        """
        return self._sql.execute(query, (deployment['id'], deployment['databases'], str(deployment['queries']), deployment['method'], deployment['status'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), deployment['scheduled'], deployment['scheduled'], deployment['url'], deployment['environment'], deployment['group_id']))

    def put(self, deployment):
        query = """
            UPDATE deployments_basic
            SET `environment_id` = (SELECT id FROM environments WHERE name = %s AND group_id = %s),
                `databases` = %s,
                `queries` = %s,
                `method` = %s,
                `status` = IF (%s != '', 'SCHEDULED', 'CREATED'),
                `scheduled` = IF(%s = '', NULL, %s)
            WHERE id = %s
        """
        self._sql.execute(query, (deployment['environment'], deployment['group_id'], deployment['databases'], deployment['queries'], deployment['method'], deployment['scheduled'], deployment['scheduled'], deployment['scheduled'], deployment['execution_id']))

    def updateStatus(self, deployment_id, status, stopped=None):
        if stopped is None:
            query = "UPDATE deployments_basic SET `status` = %s WHERE id = %s"
            self._sql.execute(query, (status, deployment_id))
        else:
            query = "UPDATE deployments_basic SET `status` = %s, `stopped` = %s WHERE id = %s"
            self._sql.execute(query, (status, stopped, deployment_id))

    def getExecutions(self, deployment_id):
        query = """
            SELECT b.id, e.name AS 'environment', b.method, b.status, b.created, b.scheduled, b.started, b.ended, CONCAT(TIMEDIFF(b.ended, b.started)) AS 'overall'
            FROM deployments_basic b
            LEFT JOIN environments e ON e.id = b.environment_id
            WHERE b.deployment_id = %s
            ORDER BY b.created DESC;
        """
        return self._sql.execute(query, (deployment_id))

    def setPublic(self, execution_id, public):
        query = """
            UPDATE deployments_basic
            SET public = %s
            WHERE id = %s
        """
        return self._sql.execute(query, (public, execution_id))

    def getUser(self, execution_id):
        query = """
            SELECT u.id, u.group_id
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id
            JOIN users u ON u.id = d.user_id
            WHERE b.id = %s
        """
        return self._sql.execute(query, (execution_id))

    def getPid(self, execution_id):
        query = """
            SELECT pid
            FROM deployments_basic
            WHERE id = %s
        """
        return self._sql.execute(query, (execution_id))

    def getScheduled(self):
        query = """
            SELECT b.id AS 'execution_id', 'BASIC' AS 'mode', u.id AS 'user_id', u.username AS 'username', g.id AS 'group_id', e.name AS 'environment', b.databases, b.queries, b.method, b.url, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_limit AS 'execution_limit', g.deployments_execution_concurrent AS 'concurrent_executions'
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id
            JOIN environments e ON e.id = b.environment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE b.status = 'SCHEDULED'
            AND %s >= b.scheduled
        """
        return self._sql.execute(query, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def getExecutionsN(self, execution_ids):
        query = """
            SELECT b.id AS 'execution_id', 'BASIC' AS 'mode', u.id AS 'user_id', u.username AS 'username', g.id AS 'group_id', e.name AS 'environment', b.databases, b.queries, b.method, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_limit AS 'execution_limit', b.url
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id
            JOIN environments e ON e.id = b.environment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE b.id IN(%s)
        """
        return self._sql.execute(query, (execution_ids))

    def setError(self, execution_id, error):
        query = """
            UPDATE deployments_basic 
            SET status = 'FAILED', 
            progress = '{{"error": "{}"}}', 
            ended = %s, 
            error = 1 
            WHERE id = %s
        """.format(error)
        return self._sql.execute(query, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), execution_id))