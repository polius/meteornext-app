#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Deployments_Failed:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, user_id, deployment_id):
        query = """
            SELECT f.* 
            FROM deployments_failed f
            JOIN deployments d ON d.id = f.deployment_id AND d.user_id = %s 
            WHERE f.deployment_id = %s
        """
        return self._mysql.execute(query, (user_id, deployment_id))

    def post(self, user_id, deployment):
        query = """
            INSERT INTO deployments_failed (deployment_id, error) 
            SELECT id, %s
            FROM deployments
            WHERE user_id = %s
            AND id = %s
        """
        self._mysql.execute(query, (deployment['error'], user_id, deployment['id']))

    def put(self, user_id, deployment):
        query = """
            UPDATE deployments_failed 
            SET error = %s
            WHERE user_id = %s
            AND id = %s
        """
        self._mysql.execute(query, (deployment['error'], user_id, deployment['id']))

    def delete(self, user_id, environment):
        query = """
            DELETE f
            FROM deployments_failed f
            JOIN deployments d ON d.id = f.deployment_id AND d.id = %s AND d.user_id = %s
        """
        self._mysql.execute(query, (deployment['id'], user_id))

    def remove(self, user_id):
        query = """
            DELETE f
            FROM deployments_failed p
            JOIN deployments d ON d.id = b.deployment_id AND d.user_id = %s
        """
        self._mysql.execute(query, (user_id))