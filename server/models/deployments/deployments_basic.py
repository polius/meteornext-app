#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Deployments_Basic:
    def __init__(self, sql):
        self._sql = sql

    def get(self, execution_id):
        query = """
            SELECT d.id, b.id AS 'execution_id', 'BASIC' AS 'mode', d.name, r.name AS 'release', e.name AS 'environment', b.databases, b.queries, b.method, b.status, b.created, b.scheduled, b.started, b.ended, CONCAT(TIMEDIFF(b.ended, b.started)) AS 'overall', b.error, b.progress, b.uri, b.engine, b.public
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id
            JOIN releases r ON r.id = d.release_id
            JOIN environments e ON e.id = b.environment_id 
            WHERE b.id = %s
        """
        return self._sql.execute(query, (execution_id))

    def post(self, deployment):
        query = """
            INSERT INTO deployments_basic (deployment_id, environment_id, `databases`, queries, method, `status`, scheduled)
            SELECT %s, e.id, %s, %s, %s, %s, IF(%s = '', NULL, %s)
            FROM environments e
            WHERE e.name = %s
        """
        return self._sql.execute(query, (deployment['id'], deployment['databases'], str(deployment['queries']), deployment['method'], deployment['status'], deployment['scheduled'], deployment['scheduled'], deployment['environment']))

    def put(self, deployment):
        query = """
            UPDATE deployments_basic
            SET `environment_id` = (SELECT id FROM environments WHERE name = %s),
                `databases` = %s,
                `queries` = %s,
                `method` = %s,
                `status` = IF (%s != '', 'SCHEDULED', 'CREATED'),
                `scheduled` = IF(%s = '', NULL, %s)
            WHERE id = %s
        """
        self._sql.execute(query, (deployment['environment'], deployment['databases'], deployment['queries'], deployment['method'], deployment['scheduled'], deployment['scheduled'], deployment['scheduled'], deployment['execution_id']))

    def getExecutions(self, deployment_id):
        query = """
            SELECT b.id, e.name AS 'environment', b.method, b.status, b.created, b.scheduled, b.started, b.ended, CONCAT(TIMEDIFF(b.ended, b.started)) AS 'overall'
            FROM deployments_basic b
            JOIN environments e ON e.id = b.environment_id
            WHERE b.deployment_id = %s
            ORDER BY b.created DESC;
        """
        return self._sql.execute(query, (deployment_id))
    
    def startExecution(self, execution_id):
        query = """
            UPDATE deployments_basic
            SET status = 'STARTING',
            scheduled = NULL
            WHERE id = %s
        """
        return self._sql.execute(query, (execution_id))

    def stopExecution(self, execution_id):
        query = """
            UPDATE deployments_basic
            SET status = 'STOPPING'
            WHERE id = %s
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
            SELECT d.user_id
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id
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
