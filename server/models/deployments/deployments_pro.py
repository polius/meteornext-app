from datetime import datetime

class Deployments_Pro:
    def __init__(self, sql):
        self._sql = sql

    def get(self, execution_id):
        query = """
            SELECT d.id, p.id AS 'execution_id', 'PRO' AS 'mode', d.name, r.name AS 'release', e.name AS 'environment', p.code, p.method, p.status, p.stopped, q.queue, p.created, p.started, p.scheduled, p.ended, CONCAT(TIMEDIFF(p.ended, p.started)) AS 'overall', p.error, p.progress, p.url, p.uri, p.engine, p.public
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

    def post(self, deployment):
        query = """
            INSERT INTO deployments_pro (deployment_id, environment_id, code, method, `status`, created, scheduled, url)
            SELECT %s, e.id, %s, %s, %s, %s, IF(%s = '', NULL, %s), %s
            FROM environments e
            WHERE e.name = %s
            AND e.group_id = %s
        """
        return self._sql.execute(query, (deployment['id'], deployment['code'], deployment['method'], deployment['status'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), deployment['scheduled'], deployment['scheduled'], deployment['url'], deployment['environment'], deployment['group_id']))

    def put(self, deployment):
        query = """
            UPDATE deployments_pro
            SET `environment_id` = (SELECT id FROM environments WHERE name = %s AND group_id = %s),
                `code` = %s,
                `method` = %s,
                `status` = IF (%s != '', 'SCHEDULED', 'CREATED'),
                `scheduled` = IF(%s = '', NULL, %s)
            WHERE id = %s
        """
        self._sql.execute(query, (deployment['environment'], deployment['group_id'], deployment['code'], deployment['method'], deployment['scheduled'], deployment['scheduled'], deployment['scheduled'], deployment['execution_id']))

    def updateStatus(self, deployment_id, status, stopped=None):
        if stopped is None:
            query = "UPDATE deployments_pro SET `status` = %s WHERE id = %s"
            self._sql.execute(query, (status, deployment_id))
        else:
            query = "UPDATE deployments_pro SET `status` = %s, `stopped` = %s WHERE id = %s"
            self._sql.execute(query, (status, stopped, deployment_id))

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
            SELECT p.id AS 'execution_id', 'PRO' AS 'mode', u.id AS 'user_id', u.username AS 'username', g.id AS 'group_id', e.name AS 'environment', p.code, p.method, p.url, p.status, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_timeout AS 'execution_timeout', g.deployments_execution_concurrent AS 'concurrent_executions'
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id
            JOIN environments e ON e.id = p.environment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE p.status = 'SCHEDULED'
            AND %s >= p.scheduled
        """
        return self._sql.execute(query, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def getExecutionsN(self, execution_ids):
        query = """
            SELECT p.id AS 'execution_id', 'PRO' AS 'mode', u.id AS 'user_id', u.username AS 'username', g.id AS 'group_id', e.name AS 'environment', p.code, p.method, p.status, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_timeout AS 'execution_timeout', p.url
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id
            JOIN environments e ON e.id = p.environment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE p.id IN(%s)
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