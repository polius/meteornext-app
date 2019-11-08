#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Deployments:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, user_id=None, deployment_id=None, search=None):
        if user_id is None and deployment_id is None:
            # Search Options
            search_user = " AND u.username = '{}'".format(search['username']) if search and 'username' in search else ''
            search_mode = " AND d.mode IN ({})".format(",".join("'{}'".format(i) for i in search['mode'])) if search and 'mode' in search else ''
            search_status = " AND d.status IN ({})".format(",".join("'{}'".format(i) for i in search['status'])) if search and 'status' in search else ''
            search_created_from = " AND d.created >= '{}'".format(search['created_from']) if search and 'created_from' in search else ''
            search_created_to = " AND d.created <= '{}'".format(search['created_to']) if search and 'created_to' in search else ''

            # Build Query
            query = """
                SELECT *, e.name AS 'environment'
                FROM
                (
                    SELECT *
                    FROM
                    (
                        SELECT d.id, db.id AS 'execution_id', u.username, d.name, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, db.created, db.started, db.ended, CONCAT(TIMEDIFF(db.ended, db.started)) AS 'overall'
                        FROM deployments_basic db
                        JOIN deployments d ON d.id = db.deployment_id AND d.deleted = 0
                        JOIN users u ON u.id = d.user_id{0}
                        JOIN groups g ON g.id = u.group_id AND g.deployments_basic = 1 
                        WHERE db.id IN (
                            SELECT MAX(id)
                            FROM deployments_basic db2
                            WHERE db2.deployment_id = db.deployment_id
                        )
                        ORDER BY db.created DESC
                        LIMIT 100
                    ) t1
                    UNION ALL
                    SELECT *
                    FROM
                    (
                        SELECT d.id, dp.id AS 'execution_id', u.username, d.name, dp.environment_id, 'PRO' AS 'mode', dp.method, dp.status, dp.created, dp.started, dp.ended, CONCAT(TIMEDIFF(dp.ended, dp.started)) AS 'overall'
                        FROM deployments_pro dp
                        JOIN deployments d ON d.id = dp.deployment_id AND d.deleted = 0
                        JOIN users u ON u.id = d.user_id{0}
                        JOIN groups g ON g.id = u.group_id AND g.deployments_pro = 1  
                        WHERE dp.id IN (
                            SELECT MAX(id)
                            FROM deployments_pro dp2
                            WHERE dp2.deployment_id = dp.deployment_id
                        )
                        ORDER BY dp.created DESC
                        LIMIT 100
                    ) t2
                ) d
                JOIN environments e ON e.id = d.environment_id
                WHERE 1=1{1}{2}{3}{4}
                ORDER BY d.created DESC
                LIMIT 100
            """.format(search_user, search_mode, search_status, search_created_from, search_created_to)
            return self._mysql.execute(query)
        elif deployment_id is not None:
            query = """
                SELECT d.id, d.execution_id, d.name, e.name AS 'environment', d.mode, d.method, d.status, d.created, d.started, d.ended, CONCAT(TIMEDIFF(d.ended, d.started)) AS 'overall'
                FROM
                (
                    SELECT d.id, db.id AS 'execution_id', d.name, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, db.created, db.started, db.ended
                    FROM deployments_basic db
                    JOIN deployments d ON d.id = db.deployment_id AND d.user_id = %s AND d.id = %s AND d.deleted = 0
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_basic = 1  
                    WHERE db.id IN (
                        SELECT MAX(id)
                        FROM deployments_basic db2
                        WHERE db2.deployment_id = db.deployment_id
                    )
                    UNION
                    SELECT d.id, dp.id AS 'execution_id', d.name, dp.environment_id, 'PRO' AS 'mode', dp.method, dp.status, dp.created, dp.started, dp.ended
                    FROM deployments_pro dp
                    JOIN deployments d ON d.id = dp.deployment_id AND d.user_id = %s AND d.id = %s AND d.deleted = 0
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_pro = 1  
                    WHERE dp.id IN (
                        SELECT MAX(id)
                        FROM deployments_pro dp2
                        WHERE dp2.deployment_id = dp.deployment_id
                    )
                ) d
                JOIN environments e ON e.id = d.environment_id
                ORDER BY id DESC
            """
            return self._mysql.execute(query, (user_id, deployment_id, user_id, deployment_id))    
        else:
            query = """
                SELECT d.id, d.execution_id, d.name, e.name AS 'environment', d.mode, d.method, d.status, d.created, d.started, d.ended, CONCAT(TIMEDIFF(d.ended, d.started)) AS 'overall'
                FROM
                (
                    SELECT d.id, db.id AS 'execution_id', d.name, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, db.created, db.started, db.ended
                    FROM deployments_basic db
                    JOIN deployments d ON d.id = db.deployment_id AND d.user_id = %s AND d.deleted = 0
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_basic = 1 
                    WHERE db.id IN (
                        SELECT MAX(id)
                        FROM deployments_basic db2
                        WHERE db2.deployment_id = db.deployment_id
                    )
                    UNION
                    SELECT d.id, dp.id AS 'execution_id', d.name, dp.environment_id, 'PRO' AS 'mode', dp.method, dp.status, dp.created, dp.started, dp.ended
                    FROM deployments_pro dp
                    JOIN deployments d ON d.id = dp.deployment_id AND d.user_id = %s AND d.deleted = 0
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_pro = 1  
                    WHERE dp.id IN (
                        SELECT MAX(id)
                        FROM deployments_pro dp2
                        WHERE dp2.deployment_id = dp.deployment_id
                    )
                ) d
                JOIN environments e ON e.id = d.environment_id
                ORDER BY created DESC
            """
            return self._mysql.execute(query, (user_id, user_id))        

    def post(self, user_id, deployment):
        query = "INSERT INTO deployments (name, user_id) VALUES(%s, %s)"
        return self._mysql.execute(query, (deployment['name'], user_id))

    def put(self, deployment):
        query = """
            UPDATE deployments
            SET name = %s
            AND id = %s
        """
        self._mysql.execute(query, (deployment['name'], deployment['id']))

    def delete(self, user_id, deployment):
        query = """
            UPDATE deployments
            SET deleted = 1
            WHERE id = %s
            AND user_id = %s 
        """
        self._mysql.execute(query, (deployment, user_id))

    def getUser(self, deployment_id):
        query = """
            SELECT user_id
            FROM deployments
            WHERE id = %s
        """
        return self._mysql.execute(query, (deployment_id))

    def getResults(self, uri):
        query = """
            SELECT d.user_id, r.*
            FROM
            (
                SELECT deployment_id, id AS 'execution_id', 'basic' AS 'mode', engine, public
                FROM deployments_basic
                WHERE uri = %s
                UNION
                SELECT deployment_id, id AS 'execution_id', 'pro' AS 'mode', engine, public
                FROM deployments_pro
                WHERE uri = %s
            ) r
            JOIN deployments d ON d.id = r.deployment_id
        """
        return self._mysql.execute(query, (uri, uri))