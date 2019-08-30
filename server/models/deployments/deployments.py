#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Deployments:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, user_id=None, deployment_id=None):
        if user_id is None:
            return self._mysql.execute("SELECT * FROM deployments ORDER BY id DESC")
        elif deployment_id is not None:
            query = """
                SELECT d.id, d.name, e.name AS 'environment', d.mode, d.method, d.status, d.created, d.started, d.ended, d.results, d.logs
                FROM deployments d
                JOIN environments e ON e.id = d.environment_id
                WHERE d.user_id = %s
                AND d.id = %s
                ORDER BY d.id DESC
            """
            return self._mysql.execute(query, (user_id, deployment_id))    
        else:
            query = """
                SELECT d.id, d.name, e.name AS 'environment', d.mode, d.method, d.status, d.created, d.started, d.ended, d.results, d.logs
                FROM deployments d
                JOIN environments e ON e.id = d.environment_id
                WHERE d.user_id = %s
                AND d.deleted = 0 
                ORDER BY d.id DESC
            """
            return self._mysql.execute(query, (user_id))        

    def post(self, user_id, deployment):
        query = """
            INSERT INTO deployments (name, user_id, environment_id, mode, method, status) 
            SELECT %s, %s, e.id, %s, %s, %s
            FROM environments e
            JOIN groups g ON g.id = e.group_id
            JOIN users u ON u.group_id = g.id AND u.id = %s
            WHERE e.name = %s
        """
        return self._mysql.execute(query, (deployment['name'], user_id, deployment['mode'], deployment['method'], deployment['status'], user_id, deployment['environment']))

    def put(self, user_id, deployment):
        if 'name' in deployment:
            query = """
                UPDATE deployments
                SET name = %s
                WHERE user_id = %s
                AND id = %s
            """
            self._mysql.execute(query, (deployment['name'], user_id, deployment['id']))
        else:
            query = """
                UPDATE deployments
                status = %s, 
                ended = %s,
                results = %s,
                logs = %s
                WHERE user_id = %s
                AND id = %s
            """
            self._mysql.execute(query, (deployment['status'], deployment['ended'], deployment['results'], deployment['logs'], user_id, deployment['id']))

    def delete(self, user_id, deployment):
        query = """
            UPDATE deployments
            SET deleted = 1
            WHERE id = %s
            AND user_id = %s 
        """
        self._mysql.execute(query, (deployment, user_id))

    def remove(self, user_id):
        self._mysql.execute("DELETE FROM deployments WHERE user_id = %s", (user_id))

    def exist(self, user_id, deployment):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM deployments
                WHERE id = %s
                AND user_id = %s
            ) AS exist
        """
        return self._mysql.execute(query, (deployment['id'], user_id))[0]['exist'] == 1