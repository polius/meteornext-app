#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Deployments_Basic:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, user_id, deployment_id):
        query = """
            SELECT d.id, d.mode, b.id AS 'execution_id', d.name, e.name AS 'environment', b.databases, b.queries, b.method, b.start_execution, b.status, b.created, b.started, b.ended, CONCAT(TIMEDIFF(b.ended, b.started)) AS 'overall', b.error, b.progress, b.results
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s
            JOIN environments e ON e.id = b.environment_id 
            WHERE b.id = (SELECT MAX(id) FROM deployments_basic WHERE deployment_id = %s);
        """
        return self._mysql.execute(query, (user_id, deployment_id))
            
    def post(self, deployment):
        query = """
            INSERT INTO deployments_basic (deployment_id, environment_id, `databases`, queries, method, start_execution)
            SELECT %s, e.id, %s, %s, %s, %s
            FROM environments e
            WHERE e.name = %s
        """
        return self._mysql.execute(query, (deployment['id'], deployment['databases'], str(deployment['queries']), deployment['method'], '0', deployment['environment']))

    def put(self, deployment):
        query = """
            UPDATE deployments_basic
            SET `environment_id` = (SELECT id FROM environments WHERE name = %s),
                `databases` = %s,
                `queries` = %s,
                `method` = %s,
                `start_execution` = %s
            WHERE id = (SELECT id FROM (SELECT MAX(id) AS 'id' FROM deployments_basic WHERE deployment_id = %s)t);
        """
        self._mysql.execute(query, (deployment['environment'], deployment['databases'], deployment['queries'], deployment['method'], deployment['start_execution'], deployment['id']))

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

    def getExecution(self, user_id, deployment_id):
        query = """
            SELECT d.id, d.mode, b.id AS 'execution_id', d.name, e.name AS 'environment', b.databases, b.queries, b.method, b.start_execution, b.created, b.started, b.ended, b.status, b.results
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s
            JOIN environments e ON e.id = b.environment_id 
            WHERE b.id = %s
        """
        return self._mysql.execute(query, (user_id, deployment_id))
    
    def startExecution(self, user_id, deployment_id):
        query = """
            UPDATE deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s 
            SET b.start_execution = 1
            WHERE b.id = %s
        """
        return self._mysql.execute(query, (user_id, deployment_id))