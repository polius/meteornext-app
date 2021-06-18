class Deployments_Queued:
    def __init__(self, sql):
        self._sql = sql

    def build(self):
        query = """
            INSERT IGNORE INTO deployments_queued (execution_mode, execution_id)
            SELECT t.execution_mode, t.execution_id
            FROM
            (
                SELECT 'basic' AS execution_mode, id AS execution_id, created, IFNULL(scheduled, created) AS time FROM deployments_basic WHERE status = 'QUEUED'
                UNION
                SELECT 'pro' AS execution_mode, id AS execution_id, created, IFNULL(scheduled, created) AS time FROM deployments_pro WHERE status = 'QUEUED'
				ORDER BY time, created
            ) t
        """
        self._sql.execute(query)

    def getFinished(self):
        query = """
            SELECT q.id, 'basic' AS 'execution_mode', b.id AS 'execution_id', b.scheduled IS NOT NULL AS 'scheduled'
            FROM deployments_basic b
            JOIN deployments_queued q ON q.execution_mode = 'basic' AND q.execution_id = b.id
            WHERE b.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            UNION
            SELECT q.id, 'pro' AS 'execution_mode', p.id AS 'execution_id', p.scheduled IS NOT NULL AS 'scheduled'
            FROM deployments_pro p
            JOIN deployments_queued q ON q.execution_mode = 'pro' AND q.execution_id = p.id
            WHERE p.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
        """
        return self._sql.execute(query)

    def getNext(self):
        query = """
            SELECT q.execution_mode AS 'mode', q.execution_id AS 'id', q.status, g.id AS 'group', g.deployments_execution_concurrent AS 'concurrent'
            FROM (
                SELECT q.id, q.execution_mode, q.execution_id, b.status, b.deployment_id FROM deployments_queued q JOIN deployments_basic b ON b.id = q.execution_id AND q.execution_mode = 'basic' AND b.status IN('QUEUED','STARTING','IN PROGRESS','STOPPING')
                UNION ALL
                SELECT q.id, q.execution_mode, q.execution_id, p.status, p.deployment_id FROM deployments_queued q JOIN deployments_pro p ON p.id = q.execution_id AND q.execution_mode = 'pro' AND p.status IN('QUEUED','STARTING','IN PROGRESS','STOPPING')
            ) q
            JOIN deployments d ON d.id = q.deployment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            ORDER BY q.id
        """
        return self._sql.execute(query)

    def delete(self, elements):
        query = "DELETE FROM deployments_queued WHERE id IN({})".format(elements)
        self._sql.execute(query)
