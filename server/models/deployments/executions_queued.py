class Executions_Queued:
    def __init__(self, sql):
        self._sql = sql

    def build(self):
        query = """
            INSERT IGNORE INTO executions_queued (execution_id)
            SELECT id
            FROM executions
            WHERE status = 'QUEUED'
            ORDER BY COALESCE(scheduled, created)
        """
        self._sql.execute(query)

    def getFinished(self):
        query = """
            SELECT q.id, e.id AS 'execution_id', e.scheduled IS NOT NULL AS 'scheduled'
            FROM executions e
            JOIN executions_queued q ON q.execution_id = e.id
            WHERE e.status IN('SUCCESS','WARNING','FAILED','STOPPED')
        """
        return self._sql.execute(query)

    def getNext(self):
        query = """
            SELECT e.id, e.status, g.id AS 'group', g.deployments_execution_concurrent AS 'concurrent'
            FROM executions e
            JOIN executions_queued q ON q.execution_id = e.id
            JOIN deployments d ON d.id = e.deployment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE e.status IN('QUEUED','STARTING','IN PROGRESS','STOPPING')
            ORDER BY e.id
        """
        return self._sql.execute(query)

    def delete(self, elements):
        query = "DELETE FROM executions_queued WHERE id IN({})".format(elements)
        self._sql.execute(query)
