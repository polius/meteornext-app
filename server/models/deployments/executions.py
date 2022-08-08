from datetime import datetime

class Executions:
    def __init__(self, sql):
        self._sql = sql

    def get(self, uri):
        query = """
            SELECT e.id, e.deployment_id, e.mode, d.name, r.name AS 'release', env.id AS 'environment_id', env.name AS 'environment_name', env.shared AS 'environment_shared', env.secured AS 'environment_secured', e.databases, e.queries, e.code, e.method, e.status, e.stopped, q.queue, e.created, e.scheduled, es.schedule_type, es.schedule_value, es.schedule_rules, e.started, e.ended, CONCAT(TIMEDIFF(IF(e.status IN('IN PROGRESS','STOPPING'), UTC_TIMESTAMP(), e.ended), e.started)) AS 'overall', e.error, e.progress, e.url, e.uri, e.logs, d.shared, e.pid
            FROM executions e
            LEFT JOIN executions_scheduled es ON es.execution_id = e.id
            JOIN deployments d ON d.id = e.deployment_id
            LEFT JOIN releases r ON r.id = d.release_id
            LEFT JOIN environments env ON env.id = e.environment_id
            LEFT JOIN
            (
                SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                FROM executions
                JOIN (SELECT @cnt := 0) t
                WHERE status = 'QUEUED'
            ) q ON q.deployment_id = d.id
            WHERE e.uri = %s
        """
        return self._sql.execute(query, (uri))

    def post(self, user_id, execution):
        query = """
            INSERT INTO executions (`deployment_id`, `environment_id`, `mode`, `databases`, `queries`, `code`, `method`, `status`, `created`, `scheduled`, `url`, `uri`, `user_id`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (execution['deployment_id'], execution['environment_id'], execution['mode'], execution['databases'], execution['queries'], execution['code'], execution['method'], execution['status'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), execution['scheduled'], execution['url'], execution['uri'], user_id))

    def put(self, user_id, execution):
        query = """
            UPDATE executions
            SET `environment_id` = %s,
                `mode` = %s,
                `databases` = %s,
                `queries` = %s,
                `code` = %s,
                `method` = %s,
                `status` = %s,
                `scheduled` = %s,
                `user_id` = %s
            WHERE uri = %s
        """
        self._sql.execute(query, (execution['environment_id'], execution['mode'], execution['databases'], execution['queries'], execution['code'], execution['method'], execution['status'], execution['scheduled'], user_id, execution['uri']))

    def updateStatus(self, execution_id, status, extra=None):
        if extra is None:
            query = "UPDATE executions SET `status` = %s WHERE id = %s"
            self._sql.execute(query, (status, execution_id))
        elif status == 'STARTING':
            query = "UPDATE executions SET `status` = 'STARTING' WHERE id = %s AND status != 'STOPPED'"
            self._sql.execute(query, (execution_id))
        elif status == 'STOPPING':
            query = "UPDATE executions SET `status` = 'STOPPING', `stopped` = %s WHERE id = %s AND `status` IN('STARTING','IN PROGRESS')"
            self._sql.execute(query, (extra, execution_id))
        elif status == 'STOPPED':
            query = "UPDATE executions SET `status` = 'STOPPED' WHERE id = %s AND status = 'QUEUED'"
            self._sql.execute(query, (execution_id))

    def getScheduled(self):
        query = """
            SELECT e.id, d.name, r.name AS 'release', e.mode, e.uri, u.id AS 'user_id', u.username, g.id AS 'group_id', env.id AS 'environment_id', env.name AS 'environment_name', e.databases, e.queries, e.code, e.method, e.url, g.deployments_execution_concurrent AS 'concurrent_executions', g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_timeout AS 'execution_timeout'
            FROM executions e
            JOIN deployments d ON d.id = e.deployment_id
            JOIN releases r ON r.id = d.release_id
            JOIN environments env ON env.id = e.environment_id
            JOIN users u ON u.id <=> e.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE e.status = 'SCHEDULED'
            AND %s >= e.scheduled
        """
        return self._sql.execute(query, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def getExecutionsN(self, execution_ids):
        query = """
            SELECT e.id, d.name, r.name AS 'release', e.mode, u.id AS 'user_id', u2.username AS 'username', g.id AS 'group_id', env.id AS 'environment_id', env.name AS 'environment_name', e.databases, e.queries, e.code, e.method, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_timeout AS 'execution_timeout', e.url, e.uri
            FROM executions e
            JOIN deployments d ON d.id = e.deployment_id
            JOIN releases r ON r.id = d.release_id
            JOIN environments env ON env.id = e.environment_id
            JOIN users u ON u.id = e.user_id
            LEFT JOIN users u2 ON u2.id = e.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE e.id IN ({})
        """.format(execution_ids)
        return self._sql.execute(query)

    def setError(self, execution_id, error):
        query = """
            UPDATE executions 
            SET status = 'FAILED', 
            progress = '{{"error": "{}"}}', 
            ended = %s, 
            error = 1 
            WHERE id = %s
        """.format(error)
        return self._sql.execute(query, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), execution_id))