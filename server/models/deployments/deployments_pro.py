#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Deployments_Pro:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, user_id, deployment_id):
        query = """
            SELECT d.id, d.name, e.name AS 'environment', p.code, p.method, p.execution, p.execution_threads, p.start_execution
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id AND d.user_id = %s
            JOIN environments e ON e.id = p.environment_id 
            WHERE p.id = (SELECT MAX(id) FROM deployments_pro WHERE deployment_id = %s);
        """
        return self._mysql.execute(query, (user_id, deployment_id))

    def post(self, deployment):
        if deployment['execution'] == 'SEQUENTIAL':
            query = """
                INSERT INTO deployments_pro (deployment_id, environment_id, code, method, execution, start_execution)
                SELECT %s, e.id, %s, %s, %s, %s
                FROM environments e
                WHERE e.name = %s
            """
            self._mysql.execute(query, (deployment['id'], deployment['code'], deployment['method'], deployment['execution'], deployment['start_execution'], deployment['environment']))
        else:
            query = """
                INSERT INTO deployments_pro (deployment_id, environment_id, code, method, execution, execution_threads, start_execution)
                SELECT %s, e.id, %s, %s, %s, %s, %s, %s
                FROM environments e
                WHERE e.name = %s
            """
            self._mysql.execute(query, (deployment['id'], deployment['code'], deployment['method'], deployment['execution'], deployment['execution_threads'], deployment['start_execution'], deployment['environment']))

    def put(self, deployment):
        if deployment['execution'] == 'SEQUENTIAL':
            query = """
                UPDATE deployments_pro
                SET `environment_id` = (SELECT id FROM environments WHERE name = %s),
                    `code` = %s,
                    `method` = %s,
                    `execution` = %s,
                    `start_execution` = %s
                WHERE id = (SELECT id FROM (SELECT MAX(id) AS 'id' FROM deployments_pro WHERE deployment_id = %s)t);
            """
            self._mysql.execute(query, (deployment['environment'], deployment['code'], deployment['method'], deployment['execution'], deployment['start_execution'], deployment['id']))
        else:
            query = """
                UPDATE deployments_pro
                SET `environment_id` = (SELECT id FROM environments WHERE name = %s),
                    `code` = %s,
                    `method` = %s,
                    `execution` = %s,
                    `execution_threads` = %s,
                    `start_execution` = %s
                WHERE id = (SELECT id FROM (SELECT MAX(id) AS 'id' FROM deployments_pro WHERE deployment_id = %s)t);
            """
            self._mysql.execute(query, (deployment['environment'], deployment['code'], deployment['method'], deployment['execution'], deployment['execution_threads'], deployment['start_execution'], deployment['id']))

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