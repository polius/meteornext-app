#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

class Deployments_Pro:
    def __init__(self, sql):
        self._sql = sql

    def get(self, execution_id):
        query = """
            SELECT d.id, p.id AS 'execution_id', 'PRO' AS 'mode', d.name, r.name AS 'release', e.name AS 'environment', p.code, p.method, p.status, p.created, p.started, p.ended, CONCAT(TIMEDIFF(p.ended, p.started)) AS 'overall', p.error, p.progress, p.uri, p.engine, p.public
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id
            JOIN releases r ON r.id = d.release_id
            JOIN environments e ON e.id = p.environment_id 
            WHERE p.id = %s
        """
        return self._sql.execute(query, (execution_id))

    def post(self, deployment):
        query = """
            INSERT INTO deployments_pro (deployment_id, environment_id, code, method, `status`)
            SELECT %s, e.id, %s, %s, %s
            FROM environments e
            WHERE e.name = %s
        """
        return self._sql.execute(query, (deployment['id'], deployment['code'], deployment['method'], deployment['status'], deployment['environment']))

    def put(self, deployment):
        query = """
            UPDATE deployments_pro
            SET `environment_id` = (SELECT id FROM environments WHERE name = %s),
                `code` = %s,
                `method` = %s
            WHERE id = %s
        """
        self._sql.execute(query, (deployment['environment'], deployment['code'], deployment['method'], deployment['execution_id']))

    def getExecutions(self, deployment_id):
        query = """
            SELECT p.id, e.name AS 'environment', p.method, p.created, p.status, p.started, p.ended, CONCAT(TIMEDIFF(p.ended, p.started)) AS 'overall'
            FROM deployments_pro p
            JOIN environments e ON e.id = p.environment_id
            WHERE p.deployment_id = %s
            ORDER BY p.created DESC;
        """
        return self._sql.execute(query, (deployment_id))

    def startExecution(self, execution_id):
        query = """
            UPDATE deployments_pro
            SET status = 'STARTING'
            WHERE id = %s
        """
        return self._sql.execute(query, (execution_id))

    def stopExecution(self, execution_id):
        query = """
            UPDATE deployments_pro
            SET status = 'STOPPING'
            WHERE id = %s
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
            SELECT d.user_id
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id
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
            SELECT p.id AS 'execution_id', 'PRO' AS 'mode', u.username AS 'user', g.id AS 'group_id', e.name AS 'environment', p.code, p.method, g.deployments_execution_threads AS 'execution_threads', g.deployments_execution_plan_factor AS 'epf'
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id
            JOIN environments e ON e.id = p.environment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE p.status = 'SCHEDULED'
            AND NOW() >= p.scheduled
            AND d.deleted = 0;
        """
        return self._sql.execute(query)

    def setError(self, execution_id, error):
        query = """
            UPDATE deployments_basic 
            SET status = 'FAILED', 
            progress = '{{"error": "{}"}}', 
            ended = %s, 
            error = 1 
            WHERE id = %s
        """.format(error)
        return self._sql.execute(query, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), execution_id))