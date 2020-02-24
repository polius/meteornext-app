#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

class Deployments_Inbenta:
    def __init__(self, sql):
        self._sql = sql

    def get(self, execution_id):
        query = """
            SELECT d.id, i.id AS 'execution_id', 'INBENTA' AS 'mode', d.name, r.name AS 'release', e.name AS 'environment', i.products, i.schema, i.databases, i.queries, i.method, i.status, q.queue, i.created, i.scheduled, i.started, i.ended, CONCAT(TIMEDIFF(i.ended, i.started)) AS 'overall', i.error, i.progress, i.uri, i.engine, i.public
            FROM deployments_inbenta i
            JOIN deployments d ON d.id = i.deployment_id
            JOIN releases r ON r.id = d.release_id
            JOIN environments e ON e.id = i.environment_id
            LEFT JOIN
            (
                SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                FROM deployments_inbenta
                JOIN (SELECT @cnt := 0) t
                WHERE status = 'QUEUED'
            ) q ON q.deployment_id = d.id
            WHERE i.id = %s
        """
        return self._sql.execute(query, (execution_id))

    def post(self, deployment):
        products = str(deployment['products'])[1:-1].replace("'", "").replace(" ", "")
        query = """
            INSERT INTO deployments_inbenta (deployment_id, environment_id, `products`, `schema`, `databases`, queries, method, `status`, created, scheduled)
            SELECT %s, e.id, %s, %s, %s, %s, %s, %s, %s, IF(%s = '', NULL, %s)
            FROM environments e
            WHERE e.name = %s
        """
        return self._sql.execute(query, (deployment['id'], products, deployment['schema'], deployment['databases'], str(deployment['queries']), deployment['method'], deployment['status'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), deployment['scheduled'], deployment['scheduled'], deployment['environment']))

    def put(self, deployment):
        query = """
            UPDATE deployments_inbenta
            SET `environment_id` = (SELECT id FROM environments WHERE name = %s),
                `products` = %s,
                `schema` = %s,
                `databases` = %s,
                `queries` = %s,
                `method` = %s,
                `status` = IF (%s != '', 'SCHEDULED', 'CREATED'),
                `scheduled` = IF(%s = '', NULL, %s)
            WHERE id = %s
        """
        self._sql.execute(query, (deployment['environment'], deployment['products'], deployment['schema'], deployment['databases'], deployment['queries'], deployment['method'], deployment['scheduled'], deployment['scheduled'], deployment['scheduled'], deployment['execution_id']))

    def updateStatus(self, deployment_id, status):
        query = """
            UPDATE deployments_inbenta
            SET `status` = %s
            WHERE id = %s
        """
        self._sql.execute(query, (status, deployment_id))

    def getExecutions(self, deployment_id):
        query = """
            SELECT i.id, e.name AS 'environment', i.method, i.created, i.scheduled, i.status, i.started, i.ended, CONCAT(TIMEDIFF(i.ended, i.started)) AS 'overall'
            FROM deployments_inbenta i
            JOIN environments e ON e.id = i.environment_id
            WHERE i.deployment_id = %s
            ORDER BY i.created DESC;
        """
        return self._sql.execute(query, (deployment_id))

    def setPublic(self, execution_id, public):
        query = """
            UPDATE deployments_inbenta
            SET public = %s
            WHERE id = %s
        """
        return self._sql.execute(query, (public, execution_id))

    def getUser(self, execution_id):
        query = """
            SELECT d.user_id
            FROM deployments_inbenta i
            JOIN deployments d ON d.id = i.deployment_id
            WHERE i.id = %s
        """
        return self._sql.execute(query, (execution_id))

    def getPid(self, execution_id):
        query = """
            SELECT pid
            FROM deployments_inbenta
            WHERE id = %s
        """
        return self._sql.execute(query, (execution_id))

    def getScheduled(self):
        query = """
            SELECT i.id AS 'execution_id', 'INBENTA' AS 'mode', u.username AS 'user', g.id AS 'group_id', e.name AS 'environment', i.products, i.schema, i.databases, i.queries, i.method, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_limit AS 'execution_limit', g.deployments_execution_concurrent AS 'concurrent_executions'
            FROM deployments_inbenta i
            JOIN deployments d ON d.id = i.deployment_id
            JOIN environments e ON e.id = i.environment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE i.status = 'SCHEDULED'
            AND %s >= i.scheduled
            AND d.deleted = 0
        """
        return self._sql.execute(query, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def getExecutionsN(self, execution_ids):
        query = """
            SELECT i.id AS 'execution_id', 'INBENTA' AS 'mode', u.username AS 'user', g.id AS 'group_id', e.name AS 'environment', i.products, i.schema, i.databases, i.queries, i.method, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_limit AS 'execution_limit'
            FROM deployments_inbenta i
            JOIN deployments d ON d.id = i.deployment_id
            JOIN environments e ON e.id = i.environment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE d.deleted = 0
            AND i.id IN(%s)
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