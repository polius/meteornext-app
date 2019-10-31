#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Deployments_Basic:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, user_id, execution_id):
        query = """
            SELECT d.id, b.id AS 'execution_id', 'BASIC' AS 'mode', d.name, e.name AS 'environment', b.databases, b.queries, b.method, b.status, b.created, b.started, b.ended, CONCAT(TIMEDIFF(b.ended, b.started)) AS 'overall', b.error, b.progress, b.uri, b.engine, b.public
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s
            JOIN environments e ON e.id = b.environment_id 
            WHERE b.id = %s
        """
        return self._mysql.execute(query, (user_id, execution_id))

    def post(self, deployment):
        query = """
            INSERT INTO deployments_basic (deployment_id, environment_id, `databases`, queries, method, `status`)
            SELECT %s, e.id, %s, %s, %s, %s
            FROM environments e
            WHERE e.name = %s
        """
        return self._mysql.execute(query, (deployment['id'], deployment['databases'], str(deployment['queries']), deployment['method'], deployment['status'], deployment['environment']))

    def put(self, deployment):
        query = """
            UPDATE deployments_basic
            SET `environment_id` = (SELECT id FROM environments WHERE name = %s),
                `databases` = %s,
                `queries` = %s,
                `method` = %s
            WHERE id = %s
        """
        self._mysql.execute(query, (deployment['environment'], deployment['databases'], deployment['queries'], deployment['method'], deployment['execution_id']))

    def delete(self, user_id, environment):
        query = """
            DELETE b
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.id = %s AND d.user_id = %s
        """
        self._mysql.execute(query, (deployment['id'], user_id))

    def remove(self, user_id):
        query = """
            DELETE b
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s
        """
        self._mysql.execute(query, (user_id))

    def getExecutions(self, user_id, deployment_id):
        query = """
            SELECT b.id, e.name AS 'environment', b.method, b.created, b.status, b.started, b.ended
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s
            JOIN environments e ON e.id = b.environment_id
            WHERE b.deployment_id = %s
            ORDER BY b.created DESC;
        """
        return self._mysql.execute(query, (user_id, deployment_id))
    
    def startExecution(self, user_id, execution_id):
        query = """
            UPDATE deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s 
            SET b.status = 'STARTING'
            WHERE b.id = %s
        """
        return self._mysql.execute(query, (user_id, execution_id))

    def stopExecution(self, user_id, execution_id):
        query = """
            UPDATE deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s 
            SET b.status = 'STOPPING'
            WHERE b.id = %s
        """
        return self._mysql.execute(query, (user_id, execution_id))

    def setPublic(self, user_id, execution_id, public):
        query = """
            UPDATE deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s 
            SET b.public = %s
            WHERE b.id = %s
        """
        return self._mysql.execute(query, (user_id, public, execution_id))

    def getPid(self, user_id, execution_id):
        query = """
            SELECT b.pid  
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s 
            WHERE b.id = %s
        """
        return self._mysql.execute(query, (user_id, execution_id))
