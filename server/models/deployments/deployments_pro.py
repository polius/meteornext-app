#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Deployments_Pro:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, user_id, deployment_id):
        query = """
            SELECT p.* 
            FROM deployments_pro p
            JOIN deployments d ON d.id = p.deployment_id AND d.user_id = %s 
            WHERE p.deployment_id = %s
        """
        return self._mysql.execute(query, (user_id, deployment_id))

    def post(self, deployment):
        if deployment['execution'] == 'SEQUENTIAL':
            query = """
                INSERT INTO deployments_pro (deployment_id, code, execution)
                VALUES (%s, %s, %s)
            """
            self._mysql.execute(query, (deployment['id'], deployment['code'], deployment['execution']))
        else:
            query = """
                INSERT INTO deployments_pro (deployment_id, code, execution, execution_threads)
                VALUES (%s, %s, %s, %s)
            """
            self._mysql.execute(query, (deployment['id'], deployment['code'], deployment['execution'], deployment['execution_threads']))
            

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