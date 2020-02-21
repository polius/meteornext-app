#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Deployments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id=None, deployment_id=None, search=None):
        if user_id is None and deployment_id is None:
            # Search Options
            search_name = " AND d.name = '{}'".format(search['name']) if search and 'name' in search else ''
            search_release = " AND r.name = '{}'".format(search['release']) if search and 'release' in search else ''
            search_username = " AND u.username = '{}'".format(search['username']) if search and 'username' in search else ''
            search_mode = " AND d.mode IN ({})".format(",".join("'{}'".format(i) for i in search['mode'])) if search and 'mode' in search else ''
            search_status = " AND d.status IN ({})".format(",".join("'{}'".format(i) for i in search['status'])) if search and 'status' in search else ''
            search_created_from = " AND d.created >= '{}'".format(search['created_from']) if search and 'created_from' in search else ''
            search_created_to = " AND d.created <= '{}'".format(search['created_to']) if search and 'created_to' in search else ''

            # Build Query
            query = """
                SELECT *, e.name AS 'environment', r.name AS 'release'
                FROM
                (
                    SELECT *
                    FROM
                    (
                        SELECT d.id, db.id AS 'execution_id', u.username, d.name, d.release_id, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, db.created, db.scheduled, db.started, db.ended, CONCAT(TIMEDIFF(db.ended, db.started)) AS 'overall'
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
                        SELECT d.id, dp.id AS 'execution_id', u.username, d.name, d.release_id, dp.environment_id, 'PRO' AS 'mode', dp.method, dp.status, dp.created, dp.scheduled, dp.started, dp.ended, CONCAT(TIMEDIFF(dp.ended, dp.started)) AS 'overall'
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
                    UNION ALL
                    SELECT *
                    FROM
                    (
                        SELECT d.id, di.id AS 'execution_id', u.username, d.name, d.release_id, di.environment_id, 'INBENTA' AS 'mode', di.method, di.status, di.created, di.scheduled, di.started, di.ended, CONCAT(TIMEDIFF(di.ended, di.started)) AS 'overall'
                        FROM deployments_inbenta di
                        JOIN deployments d ON d.id = di.deployment_id AND d.deleted = 0
                        JOIN users u ON u.id = d.user_id{0}
                        JOIN groups g ON g.id = u.group_id AND g.deployments_inbenta = 1  
                        WHERE di.id IN (
                            SELECT MAX(id)
                            FROM deployments_inbenta di2
                            WHERE di2.deployment_id = di.deployment_id
                        )
                        ORDER BY di.created DESC
                        LIMIT 100
                    ) t3
                ) d
                JOIN environments e ON e.id = d.environment_id
                LEFT JOIN releases r ON r.id = d.release_id
                WHERE 1=1{1}{2}{3}{4}{5}{6}
                ORDER BY d.created DESC
                LIMIT 100
            """.format(search_username, search_name, search_release, search_mode, search_status, search_created_from, search_created_to)
            results = self._sql.execute(query)
        elif deployment_id is not None:
            query = """
                SELECT d.id, d.execution_id, d.name, e.name AS 'environment', r.name AS 'release', d.mode, d.method, d.status, d.created, d.scheduled, d.started, d.ended, CONCAT(TIMEDIFF(d.ended, d.started)) AS 'overall'
                FROM
                (
                    SELECT d.id, db.id AS 'execution_id', d.name, d.release_id, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, db.created, db.scheduled, db.started, db.ended
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
                    SELECT d.id, dp.id AS 'execution_id', d.name, d.release_id, dp.environment_id, 'PRO' AS 'mode', dp.method, dp.status, dp.created, dp.scheduled, dp.started, dp.ended
                    FROM deployments_pro dp
                    JOIN deployments d ON d.id = dp.deployment_id AND d.user_id = %s AND d.id = %s AND d.deleted = 0
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_pro = 1  
                    WHERE dp.id IN (
                        SELECT MAX(id)
                        FROM deployments_pro dp2
                        WHERE dp2.deployment_id = dp.deployment_id
                    )
                    UNION
                    SELECT d.id, di.id AS 'execution_id', d.name, d.release_id, di.environment_id, 'INBENTA' AS 'mode', di.method, di.status, di.created, di.scheduled, di.started, di.ended
                    FROM deployments_inbenta di
                    JOIN deployments d ON d.id = di.deployment_id AND d.user_id = %s AND d.id = %s AND d.deleted = 0
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_inbenta = 1  
                    WHERE di.id IN (
                        SELECT MAX(id)
                        FROM deployments_inbenta di2
                        WHERE di2.deployment_id = di.deployment_id
                    )
                ) d
                JOIN environments e ON e.id = d.environment_id
                LEFT JOIN releases r ON r.id = d.release_id
                WHERE r.active = 1 OR r.active IS NULL
                ORDER BY id DESC
            """
            results = self._sql.execute(query, (user_id, deployment_id, user_id, deployment_id, user_id, deployment_id))    
        else:
            query = """
                SELECT d.id, d.execution_id, d.name, e.name AS 'environment', r.name AS 'release', d.mode, d.method, d.status, d.queue, d.created, d.scheduled, d.started, d.ended, CONCAT(TIMEDIFF(d.ended, d.started)) AS 'overall'
                FROM
                (
                    SELECT d.id, db.id AS 'execution_id', d.name, d.release_id, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, q.queue, db.created, db.scheduled, db.started, db.ended
                    FROM deployments_basic db
                    JOIN deployments d ON d.id = db.deployment_id AND d.user_id = %s AND d.deleted = 0
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_basic = 1 
                    LEFT JOIN
                    (
                        SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                        FROM deployments_basic
                        JOIN (SELECT @cnt := 0) t
                        WHERE status = 'QUEUED'
                    ) q ON q.deployment_id = d.id
                    WHERE db.id IN (
                        SELECT MAX(id)
                        FROM deployments_basic db2
                        WHERE db2.deployment_id = db.deployment_id
                    )
                    UNION
                    SELECT d.id, dp.id AS 'execution_id', d.name, d.release_id, dp.environment_id, 'PRO' AS 'mode', dp.method, dp.status, q.queue, dp.created, dp.scheduled, dp.started, dp.ended
                    FROM deployments_pro dp
                    JOIN deployments d ON d.id = dp.deployment_id AND d.user_id = %s AND d.deleted = 0
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_pro = 1  
                    LEFT JOIN
                    (
                        SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                        FROM deployments_pro
                        JOIN (SELECT @cnt := 0) t
                        WHERE status = 'QUEUED'
                    ) q ON q.deployment_id = d.id
                    WHERE dp.id IN (
                        SELECT MAX(id)
                        FROM deployments_pro dp2
                        WHERE dp2.deployment_id = dp.deployment_id
                    )
                    UNION
                    SELECT d.id, di.id AS 'execution_id', d.name, d.release_id, di.environment_id, 'INBENTA' AS 'mode', di.method, di.status, q.queue, di.created, di.scheduled, di.started, di.ended
                    FROM deployments_inbenta di
                    JOIN deployments d ON d.id = di.deployment_id AND d.user_id = %s AND d.deleted = 0
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_inbenta = 1  
                    LEFT JOIN
                    (
                        SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                        FROM deployments_inbenta
                        JOIN (SELECT @cnt := 0) t
                        WHERE status = 'QUEUED'
                    ) q ON q.deployment_id = d.id
                    WHERE di.id IN (
                        SELECT MAX(id)
                        FROM deployments_inbenta di2
                        WHERE di2.deployment_id = di.deployment_id
                    )
                ) d
                JOIN environments e ON e.id = d.environment_id
                LEFT JOIN releases r ON r.id = d.release_id
                WHERE r.active = 1 OR r.active IS NULL
                ORDER BY created DESC
            """
            results = self._sql.execute(query, (user_id, user_id, user_id))

        return results

    def post(self, user_id, deployment):
        query = """
            INSERT INTO deployments (name, release_id, user_id)
            SELECT %s, id, %s
            FROM releases
            WHERE name = %s
            AND user_id = %s
        """
        return self._sql.execute(query, (deployment['name'], user_id, deployment['release'], user_id))

    def putName(self, user_id, deployment):
        query = """
            UPDATE deployments
            SET name = %s
            WHERE id = %s
            AND user_id = %s
        """
        self._sql.execute(query, (deployment['name'], deployment['id'], user_id))

    def putRelease(self, user_id, deployment):
        query = """
            UPDATE deployments, releases
            SET deployments.release_id = releases.id
            WHERE deployments.id = %s
            AND deployments.user_id = %s
            AND releases.name = %s
            AND releases.user_id = %s
        """
        self._sql.execute(query, (deployment['id'], user_id, deployment['release'], user_id))

    def delete(self, user_id, deployment):
        query = """
            UPDATE deployments
            SET deleted = 1
            WHERE id = %s
            AND user_id = %s 
        """
        self._sql.execute(query, (deployment, user_id))

    def getUser(self, deployment_id):
        query = """
            SELECT user_id
            FROM deployments
            WHERE id = %s
        """
        return self._sql.execute(query, (deployment_id))

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
                UNION
                SELECT deployment_id, id AS 'execution_id', 'inbenta' AS 'mode', engine, public
                FROM deployments_inbenta
                WHERE uri = %s
            ) r
            JOIN deployments d ON d.id = r.deployment_id
        """
        return self._sql.execute(query, (uri, uri, uri))

    def getPending(self):
        query = """
            SELECT SUBSTRING_INDEX(GROUP_CONCAT(CONCAT(q.mode, q.execution_id) SEPARATOR ','), ',', g.deployments_execution_concurrent) AS 'executions'
            FROM
            (
                SELECT deployment_id, id AS execution_id, 'b' AS 'mode', created FROM deployments_basic WHERE status = 'QUEUED'
                UNION
                SELECT deployment_id, id AS execution_id, 'p' AS 'mode', created FROM deployments_pro WHERE status = 'QUEUED'
                UNION
                SELECT deployment_id, id AS execution_id, 'i' AS 'mode', created FROM deployments_inbenta WHERE status = 'QUEUED'
                ORDER BY created
            ) q
            JOIN deployments d ON d.id = q.deployment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            GROUP BY u.group_id;
        """
        return self._sql.execute(query)

    def removeRelease(self, release_id):
        query = """
            UPDATE deployments 
            SET release_id = NULL 
            WHERE release_id = %s
        """
        return self._sql.execute(query, (release_id))