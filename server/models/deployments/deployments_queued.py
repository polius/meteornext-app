#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
                UNION
                SELECT 'inbenta' AS execution_mode, id AS execution_id, created, IFNULL(scheduled, created) AS time FROM deployments_inbenta WHERE status = 'QUEUED'
				ORDER BY time, created
            ) t
        """
        self._sql.execute(query)

    def getFinished(self):
        query = """
            SELECT q.id, 'basic' AS 'execution_mode', b.id AS 'execution_id'
            FROM deployments_basic b
            JOIN deployments_queued q ON q.execution_mode = 'basic' AND q.execution_id = b.id
            WHERE b.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            UNION
            SELECT q.id, 'pro' AS 'execution_mode', p.id AS 'execution_id'
            FROM deployments_pro p
            JOIN deployments_queued q ON q.execution_mode = 'pro' AND q.execution_id = p.id
            WHERE p.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            UNION
            SELECT q.id, 'inbenta' AS 'execution_mode', i.id AS 'execution_id'
            FROM deployments_inbenta i
            JOIN deployments_queued q ON q.execution_mode = 'inbenta' AND q.execution_id = i.id
            WHERE i.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
        """
        return self._sql.execute(query)

    def getNext(self):
        query = """
            SELECT SUBSTRING_INDEX(GROUP_CONCAT(CONCAT(q.execution_mode, '|', q.execution_id, '|', q.status) ORDER BY q.id SEPARATOR ','), ',', g.deployments_execution_concurrent) AS 'executions'
            FROM
            (
                SELECT q.id, q.execution_mode, q.execution_id, b.status, b.deployment_id FROM deployments_queued q JOIN deployments_basic b ON b.id = q.execution_id AND q.execution_mode = 'basic'
                UNION
                SELECT q.id, q.execution_mode, q.execution_id, p.status, p.deployment_id FROM deployments_queued q JOIN deployments_pro p ON p.id = q.execution_id AND q.execution_mode = 'pro'
                UNION
                SELECT q.id, q.execution_mode, q.execution_id, i.status, i.deployment_id FROM deployments_queued q JOIN deployments_inbenta i ON i.id = q.execution_id AND q.execution_mode = 'inbenta'
                ORDER BY id
            ) q
            JOIN deployments d ON d.id = q.deployment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            GROUP BY g.id
        """
        return self._sql.execute(query)

    def delete(self, elements):
        query = "DELETE FROM deployments_queued WHERE id IN(%s)"
        self._sql.execute(query, (elements))
