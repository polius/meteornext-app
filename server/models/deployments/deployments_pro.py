from datetime import datetime

class Deployments_Pro:
    def __init__(self, sql):
        self._sql = sql

    def get(self, execution_id):
        query = """
            SELECT d.id, p.id AS 'execution_id', 'PRO' AS 'mode', d.name, r.name AS 'release', e.id AS 'environment_id', e.name AS 'environment_name', p.code, p.method, p.status, p.stopped, q.queue, p.created, p.started, p.scheduled, p.ended, CONCAT(TIMEDIFF(p.ended, p.started)) AS 'overall', p.error, p.progress, p.url, p.uri, p.engine, p.public
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id
            LEFT JOIN releases r ON r.id = d.release_id
            LEFT JOIN environments e ON e.id = p.environment_id
            LEFT JOIN
            (
                SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                FROM deployments_pro
                JOIN (SELECT @cnt := 0) t
                WHERE status = 'QUEUED'
            ) q ON q.deployment_id = d.id
            WHERE p.id = %s
        """
        return self._sql.execute(query, (execution_id))

    def post(self, user_id, deployment):
        query = """
            INSERT INTO deployments_pro (deployment_id, environment_id, code, method, `status`, created, scheduled, url, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (deployment['id'], deployment['environment'], deployment['code'], deployment['method'], deployment['status'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), deployment['scheduled'], deployment['url'], user_id))

    def put(self, user_id, deployment):
        query = """
            UPDATE deployments_pro
            SET `environment_id` = %s,
                `code` = %s,
                `method` = %s,
                `status` = %s,
                `scheduled` = %s,
                `user_id` = %s
            WHERE id = %s
        """
        status = 'CREATED' if deployment['scheduled'] is None else 'SCHEDULED'
        self._sql.execute(query, (deployment['environment'], deployment['code'], deployment['method'], status, deployment['scheduled'], user_id, deployment['execution_id']))

    def updateStatus(self, deployment_id, status, extra=None):
        if extra is None:
            query = "UPDATE deployments_pro SET `status` = %s WHERE id = %s"
            self._sql.execute(query, (status, deployment_id))
        elif status == 'STARTING':
            query = "UPDATE deployments_pro SET `status` = %s WHERE id = %s AND status != 'STOPPED'"
            self._sql.execute(query, (status, deployment_id))
        elif status == 'STOPPING':
            query = "UPDATE deployments_pro SET `status` = %s, `stopped` = %s WHERE id = %s AND `status` IN('STARTING','IN PROGRESS')"
            self._sql.execute(query, (status, extra, deployment_id))
        elif status == 'STOPPED':
            query = "UPDATE deployments_pro SET `status` = 'STOPPED' WHERE id = %s AND status = 'QUEUED'"
            self._sql.execute(query, (deployment_id))

    def getExecutions(self, execution_id):
        query = """
            SELECT p.id, e.name AS 'environment', p.method, p.created, p.status, p.started, p.ended, CONCAT(TIMEDIFF(p.ended, p.started)) AS 'overall'
            FROM deployments_pro p
            JOIN deployments_pro p2 ON p2.deployment_id = p.deployment_id AND p2.id = %s
            LEFT JOIN environments e ON e.id = p.environment_id
            ORDER BY p.created DESC;
        """
        return self._sql.execute(query, (execution_id))

    def setPublic(self, execution_id, public):
        query = """
            UPDATE deployments_pro
            SET public = %s
            WHERE id = %s
        """
        return self._sql.execute(query, (public, execution_id))

    def getUser(self, execution_id):
        query = """
            SELECT u.id, u.group_id
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id
            JOIN users u ON u.id = d.user_id
            WHERE p.id = %s
        """
        return self._sql.execute(query, (execution_id))

    def getPid(self, execution_id):
        query = """
            SELECT pid
            FROM deployments_pro
            WHERE id = %s
        """
        return self._sql.execute(query, (execution_id))

    def getScheduled(self):
        query = """
            SELECT p.id AS 'execution_id', 'PRO' AS 'mode', u.id AS 'user_id', u.username AS 'username', g.id AS 'group_id', e.id AS 'environment_id', e.name AS 'environment_name', p.code, p.method, p.url, p.status, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_timeout AS 'execution_timeout', g.deployments_execution_concurrent AS 'concurrent_executions'
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id
            JOIN environments e ON e.id = p.environment_id
            JOIN users u ON u.id <=> p.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE p.status = 'SCHEDULED'
            AND %s >= p.scheduled
        """
        return self._sql.execute(query, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def getExecutionsN(self, execution_ids):
        query = """
            SELECT p.id AS 'execution_id', 'PRO' AS 'mode', u.id AS 'user_id', u2.username AS 'username', g.id AS 'group_id', e.id AS 'environment_id', e.name AS 'environment_name', p.code, p.method, p.status, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_timeout AS 'execution_timeout', p.url
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id
            JOIN environments e ON e.id = p.environment_id
            JOIN users u ON u.id = d.user_id
            LEFT JOIN users u2 ON u2.id = p.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE p.id IN (%s)
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