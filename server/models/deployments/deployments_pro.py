#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Deployments_Pro:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, user_id, execution_id):
        query = """
            SELECT d.id, p.id AS 'execution_id', 'PRO' AS 'mode', d.name, e.name AS 'environment', p.code, p.method, p.status, p.created, p.started, p.ended, CONCAT(TIMEDIFF(p.ended, p.started)) AS 'overall', p.error, p.progress, p.uri, p.engine, p.public
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id AND d.user_id = %s
            JOIN environments e ON e.id = p.environment_id 
            WHERE p.id = %s
        """
        return self._mysql.execute(query, (user_id, execution_id))

    def post(self, deployment):
        query = """
            INSERT INTO deployments_pro (deployment_id, environment_id, code, method, `status`)
            SELECT %s, e.id, %s, %s, %s
            FROM environments e
            WHERE e.name = %s
        """
        return self._mysql.execute(query, (deployment['id'], deployment['code'], deployment['method'], deployment['status'], deployment['environment']))

    def put(self, deployment):
        query = """
            UPDATE deployments_pro
            SET `environment_id` = (SELECT id FROM environments WHERE name = %s),
                `code` = %s,
                `method` = %s
            WHERE id = %s
        """
        self._mysql.execute(query, (deployment['environment'], deployment['code'], deployment['method'], deployment['execution_id']))

    def delete(self, user_id, environment):
        query = """
            DELETE p
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id AND d.id = %s AND d.user_id = %s
        """
        self._mysql.execute(query, (deployment['id'], user_id))

    def remove(self, user_id):
        query = """
            DELETE p
            FROM deployments_pro p
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s
        """
        self._mysql.execute(query, (user_id))

    def getExecutions(self, user_id, deployment_id):
        query = """
            SELECT p.id, e.name AS 'environment', p.method, p.created, p.status, p.started, p.ended
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id AND d.user_id = %s
            JOIN environments e ON e.id = p.environment_id
            WHERE p.deployment_id = %s
            ORDER BY p.created DESC;
        """
        return self._mysql.execute(query, (user_id, deployment_id))

    def startExecution(self, user_id, execution_id):
        query = """
            UPDATE deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id AND d.user_id = %s 
            SET p.status = 'STARTING'
            WHERE p.id = %s
        """
        return self._mysql.execute(query, (user_id, execution_id))

    def stopExecution(self, user_id, execution_id):
        query = """
            UPDATE deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id AND d.user_id = %s 
            SET p.status = 'STOPPING'
            WHERE p.id = %s
        """
        return self._mysql.execute(query, (user_id, execution_id))

    def setPublic(self, user_id, execution_id, public):
        query = """
            UPDATE deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id AND d.user_id = %s 
            SET p.public = %s
            WHERE p.id = %s
        """
        return self._mysql.execute(query, (user_id, public, execution_id))

    def getPid(self, user_id, execution_id):
        query = """
            SELECT p.pid  
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id AND d.user_id = %s 
            WHERE p.id = %s
        """
        return self._mysql.execute(query, (user_id, execution_id))
