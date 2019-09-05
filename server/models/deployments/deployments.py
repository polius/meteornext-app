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
                SELECT d.id, d.name, e.name AS 'environment', d.mode, d.method, d.status, d.created, d.started, d.ended
                FROM
                (
                    SELECT d.id, d.name, db.environment_id, d.mode, db.method, db.status, db.created, db.started, db.ended
                    FROM deployments_basic db
                    JOIN deployments d ON d.id = db.deployment_id AND d.user_id = %s AND d.id = %s
                    WHERE db.id IN (
                        SELECT MAX(id)
                        FROM deployments_basic
                        GROUP BY deployment_id
                    )
                    UNION
                    SELECT d.id, d.name, dp.environment_id, d.mode, dp.method, dp.status, dp.created, dp.started, dp.ended
                    FROM deployments_pro dp
                    JOIN deployments d ON d.id = dp.deployment_id AND d.user_id = %s AND d.id = %s
                    WHERE dp.id IN (
                        SELECT MAX(id)
                        FROM deployments_pro
                        GROUP BY deployment_id
                    )
                    ORDER BY id DESC
                ) d
                JOIN environments e ON e.id = d.environment_id
            """
            return self._mysql.execute(query, (user_id, deployment_id, user_id, deployment_id))    
        else:
            query = """
                SELECT d.id, d.name, e.name AS 'environment', d.mode, d.method, d.status, d.created, d.started, d.ended
                FROM
                (
                    SELECT d.id, d.name, db.environment_id, d.mode, db.method, db.status, db.created, db.started, db.ended
                    FROM deployments_basic db
                    JOIN deployments d ON d.id = db.deployment_id AND d.user_id = %s
                    WHERE db.id IN (
                        SELECT MAX(id)
                        FROM deployments_basic
                        GROUP BY deployment_id
                    )
                    UNION
                    SELECT d.id, d.name, dp.environment_id, d.mode, dp.method, dp.status, dp.created, dp.started, dp.ended
                    FROM deployments_pro dp
                    JOIN deployments d ON d.id = dp.deployment_id AND d.user_id = %s
                    WHERE dp.id IN (
                        SELECT MAX(id)
                        FROM deployments_pro
                        GROUP BY deployment_id
                    )
                    ORDER BY id DESC
                ) d
                JOIN environments e ON e.id = d.environment_id
            """
            return self._mysql.execute(query, (user_id, user_id))        

    def post(self, user_id, deployment):
        query = "INSERT INTO deployments (name, user_id, mode) VALUES(%s, %s, %s)"
        return self._mysql.execute(query, (deployment['name'], user_id, deployment['mode']))

    def put(self, user_id, deployment):
        query = """
            UPDATE deployments
            SET name = %s
            WHERE user_id = %s
            AND id = %s
        """
        self._mysql.execute(query, (deployment['name'], user_id, deployment['id']))

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