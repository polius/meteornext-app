#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Deployments_Basic:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, user_id, deployment_id):
        query = """
            SELECT d.id, d.name, e.name, b.databases, b.queries, d.method, b.execution, b.execution_threads
            FROM deployments_basic b
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s
            JOIN environments e ON e.id = d.environment_id 
            WHERE b.deployment_id = %s
        """
        return self._mysql.execute(query, (user_id, deployment_id))

    def post(self, deployment):
        if deployment['execution'] == 'SEQUENTIAL':
            query = """
                INSERT INTO deployments_basic (deployment_id, `databases`, queries, execution) 
                VALUES(%s, %s, %s, %s)
            """
            self._mysql.execute(query, (deployment['id'], deployment['databases'], deployment['queries'], deployment['execution']))
        else:
            query = """
                INSERT INTO deployments_basic (deployment_id, `databases`, queries, execution, execution_threads) 
                VALUES(%s, %s, %s, %s, %s)
            """
            self._mysql.execute(query, (deployment['id'], deployment['databases'], deployment['queries'], deployment['execution'], deployment['execution_threads']))

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