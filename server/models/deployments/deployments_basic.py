from datetime import datetime

class Deployments_Basic:
    def __init__(self, sql):
        self._sql = sql

    def get(self, execution_id):
        query = """
            SELECT d.id, b.id AS 'execution_id', 'BASIC' AS 'mode', d.name, r.name AS 'release', e.id AS 'environment_id', e.name AS 'environment_name', b.databases, b.queries, b.method, b.status, b.stopped, q.queue, b.created, b.scheduled, b.started, b.ended, CONCAT(TIMEDIFF(b.ended, b.started)) AS 'overall', b.error, b.progress, b.url, b.uri, b.engine, b.public
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

    def post(self, user_id, deployment):
        query = """
            INSERT INTO deployments_basic (deployment_id, environment_id, `databases`, queries, method, `status`, created, scheduled, url, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (deployment['id'], deployment['environment'], deployment['databases'], str(deployment['queries']), deployment['method'], deployment['status'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), deployment['scheduled'], deployment['url'], user_id))

    def put(self, user_id, deployment):
        query = """
            UPDATE deployments_basic
            SET `environment_id` = %s,
                `databases` = %s,
                `queries` = %s,
                `method` = %s,
                `status` = %s,
                `scheduled` = %s,
                `user_id` = %s
            WHERE id = %s
        """
        status = 'CREATED' if deployment['scheduled'] is None else 'SCHEDULED'
        self._sql.execute(query, (deployment['environment'], deployment['databases'], deployment['queries'], deployment['method'], status, deployment['scheduled'], user_id, deployment['execution_id']))

    def updateStatus(self, deployment_id, status, extra=None):
        if extra is None:
            query = "UPDATE deployments_basic SET `status` = %s WHERE id = %s"
            self._sql.execute(query, (status, deployment_id))
        elif status == 'STARTING':
            query = "UPDATE deployments_basic SET `status` = %s WHERE id = %s AND status != 'STOPPED'"
            self._sql.execute(query, (status, deployment_id))
        elif status == 'STOPPING':
            query = "UPDATE deployments_basic SET `status` = %s, `stopped` = %s WHERE id = %s"
            self._sql.execute(query, (status, extra, deployment_id))

    def getExecutions(self, execution_id):
        query = """
            SELECT b.id, e.name AS 'environment', b.method, b.status, b.created, b.scheduled, b.started, b.ended, CONCAT(TIMEDIFF(b.ended, b.started)) AS 'overall'
            FROM deployments_basic b
            JOIN deployments_basic b2 ON b2.deployment_id = b.deployment_id AND b2.id = %s
            LEFT JOIN environments e ON e.id = b.environment_id
            ORDER BY b.created DESC;
        """
        return self._sql.execute(query, (execution_id))

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
            SELECT b.id AS 'execution_id', 'BASIC' AS 'mode', u.id AS 'user_id', u.username AS 'username', g.id AS 'group_id', e.id AS 'environment_id', e.name AS 'environment_name', b.databases, b.queries, b.method, b.url, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_timeout AS 'execution_timeout', g.deployments_execution_concurrent AS 'concurrent_executions'
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id
            JOIN environments e ON e.id = b.environment_id
            JOIN users u ON u.id <=> b.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE b.status = 'SCHEDULED'
            AND %s >= b.scheduled
        """
        return self._sql.execute(query, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def getExecutionsN(self, execution_ids):
        query = """
            SELECT b.id AS 'execution_id', 'BASIC' AS 'mode', u.id AS 'user_id', u2.username AS 'username', g.id AS 'group_id', e.id AS 'environment_id', e.name AS 'environment_name', b.databases, b.queries, b.method, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_timeout AS 'execution_timeout', b.url
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id
            JOIN environments e ON e.id = b.environment_id
            JOIN users u ON u.id = d.user_id
            LEFT JOIN users u2 ON u2.id = b.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE b.id IN (%s)
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