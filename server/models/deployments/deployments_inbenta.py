#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Deployments_Inbenta:
    def __init__(self, sql):
        self._sql = sql

    def get(self, execution_id):
        query = """
            SELECT d.id, i.id AS 'execution_id', 'INBENTA' AS 'mode', d.name, e.name AS 'environment', i.products, i.schema, i.databases, i.queries, i.method, i.status, i.created, i.started, i.ended, CONCAT(TIMEDIFF(i.ended, i.started)) AS 'overall', i.error, i.progress, i.uri, i.engine, i.public
            FROM deployments_inbenta i
            JOIN deployments d ON d.id = i.deployment_id
            JOIN environments e ON e.id = i.environment_id 
            WHERE i.id = %s
        """
        return self._sql.execute(query, (execution_id))

    def post(self, deployment):
        products = str(deployment['products'])[1:-1].replace("'", "").replace(" ", "")
        query = """
            INSERT INTO deployments_inbenta (deployment_id, environment_id, `products`, `schema`, `databases`, queries, method, `status`)
            SELECT %s, e.id, %s, %s, %s, %s, %s, %s
            FROM environments e
            WHERE e.name = %s
        """
        return self._sql.execute(query, (deployment['id'], products, deployment['schema'], deployment['databases'], str(deployment['queries']), deployment['method'], deployment['status'], deployment['environment']))

    def put(self, deployment):
        query = """
            UPDATE deployments_inbenta
            SET `environment_id` = (SELECT id FROM environments WHERE name = %s),
                `products` = %s,
                `schema` = %s,
                `databases` = %s,
                `queries` = %s,
                `method` = %s
            WHERE id = %s
        """
        self._sql.execute(query, (deployment['environment'], deployment['products'], deployment['schema'], deployment['databases'], deployment['queries'], deployment['method'], deployment['execution_id']))

    def getExecutions(self, deployment_id):
        query = """
            SELECT i.id, e.name AS 'environment', i.method, i.created, i.status, i.started, i.ended, CONCAT(TIMEDIFF(i.ended, i.started)) AS 'overall'
            FROM deployments_inbenta i
            JOIN environments e ON e.id = i.environment_id
            WHERE i.deployment_id = %s
            ORDER BY i.created DESC;
        """
        return self._sql.execute(query, (deployment_id))
    
    def startExecution(self, execution_id):
        query = """
            UPDATE deployments_inbenta
            SET status = 'STARTING'
            WHERE id = %s
        """
        return self._sql.execute(query, (execution_id))

    def stopExecution(self, execution_id):
        query = """
            UPDATE deployments_inbenta
            SET status = 'STOPPING'
            WHERE id = %s
        """
        return self._sql.execute(query, (execution_id))

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
