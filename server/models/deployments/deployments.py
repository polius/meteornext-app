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
                    (
                        SELECT d.id, db.id AS 'execution_id', u.username, d.name, d.release_id, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, db.created, db.scheduled, db.started, db.ended, CONCAT(TIMEDIFF(db.ended, db.started)) AS 'overall'
                        FROM deployments_basic db
                        JOIN deployments d ON d.id = db.deployment_id
                        JOIN users u ON u.id = d.user_id{0}
                        WHERE db.id IN (
                            SELECT MAX(id)
                            FROM deployments_basic db2
                            WHERE db2.deployment_id = db.deployment_id
                        )
                        ORDER BY db.created DESC
                        LIMIT 1000
                    )
                    UNION ALL
                    (
                        SELECT d.id, dp.id AS 'execution_id', u.username, d.name, d.release_id, dp.environment_id, 'PRO' AS 'mode', dp.method, dp.status, dp.created, dp.scheduled, dp.started, dp.ended, CONCAT(TIMEDIFF(dp.ended, dp.started)) AS 'overall'
                        FROM deployments_pro dp
                        JOIN deployments d ON d.id = dp.deployment_id
                        JOIN users u ON u.id = d.user_id{0}
                        WHERE dp.id IN (
                            SELECT MAX(id)
                            FROM deployments_pro dp2
                            WHERE dp2.deployment_id = dp.deployment_id
                        )
                        ORDER BY dp.created DESC
                        LIMIT 1000
                    )
                ) d
                LEFT JOIN environments e ON e.id = d.environment_id
                LEFT JOIN releases r ON r.id = d.release_id
                WHERE 1=1{1}{2}{3}{4}{5}{6}
                ORDER BY d.created DESC
                LIMIT 1000
            """.format(search_username, search_name, search_release, search_mode, search_status, search_created_from, search_created_to)
            results = self._sql.execute(query)
        elif deployment_id is not None:
            query = """
                SELECT d.id, d.execution_id, d.name, e.name AS 'environment', r.name AS 'release', d.mode, d.method, d.status, d.created, d.scheduled, d.started, d.ended, CONCAT(TIMEDIFF(d.ended, d.started)) AS 'overall'
                FROM
                (
                    SELECT d.id, db.id AS 'execution_id', d.name, d.release_id, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, db.created, db.scheduled, db.started, db.ended
                    FROM deployments_basic db
                    JOIN deployments d ON d.id = db.deployment_id AND d.user_id = %(user_id)s AND d.id = %(deployment_id)s
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_basic = 1  
                    WHERE db.id IN (
                        SELECT MAX(id)
                        FROM deployments_basic db2
                        WHERE db2.deployment_id = db.deployment_id
                    )
                    UNION ALL
                    SELECT d.id, dp.id AS 'execution_id', d.name, d.release_id, dp.environment_id, 'PRO' AS 'mode', dp.method, dp.status, dp.created, dp.scheduled, dp.started, dp.ended
                    FROM deployments_pro dp
                    JOIN deployments d ON d.id = dp.deployment_id AND d.user_id = %(user_id)s AND d.id = %(deployment_id)s
                    JOIN users u ON u.id = d.user_id
                    JOIN groups g ON g.id = u.group_id AND g.deployments_pro = 1  
                    WHERE dp.id IN (
                        SELECT MAX(id)
                        FROM deployments_pro dp2
                        WHERE dp2.deployment_id = dp.deployment_id
                    )
                ) d
                LEFT JOIN environments e ON e.id = d.environment_id
                LEFT JOIN releases r ON r.id = d.release_id
                WHERE r.active = 1 OR r.active IS NULL
                ORDER BY id DESC
            """
            results = self._sql.execute(query, {'user_id': user_id, 'deployment_id': deployment_id})    
        else:
            query = """
                SELECT d.id, d.execution_id, d.name, e.name AS 'environment', r.name AS 'release', d.mode, d.method, d.status, d.queue, d.created, d.scheduled, d.started, d.ended, CONCAT(TIMEDIFF(d.ended, d.started)) AS 'overall'
                FROM
                (
                    (
                        SELECT d.id, db.id AS 'execution_id', d.name, d.release_id, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, q.queue, db.created, db.scheduled, db.started, db.ended
                        FROM deployments_basic db
                        JOIN deployments d ON d.id = db.deployment_id AND d.user_id = %(user_id)s
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
                        ORDER BY db.created DESC
                        LIMIT 1000
                    )
                    UNION ALL
                    (
                        SELECT d.id, dp.id AS 'execution_id', d.name, d.release_id, dp.environment_id, 'PRO' AS 'mode', dp.method, dp.status, q.queue, dp.created, dp.scheduled, dp.started, dp.ended
                        FROM deployments_pro dp
                        JOIN deployments d ON d.id = dp.deployment_id AND d.user_id = %(user_id)s
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
                        ORDER BY dp.created DESC
                        LIMIT 1000
                    )
                ) d
                LEFT JOIN environments e ON e.id = d.environment_id
                LEFT JOIN releases r ON r.id = d.release_id
                WHERE r.active = 1 OR r.active IS NULL
                ORDER BY created DESC
                LIMIT 1000
            """
            results = self._sql.execute(query, {"user_id": user_id})

        return results

    def post(self, user_id, deployment):
        query = """
            INSERT INTO deployments (name, release_id, user_id)
            SELECT %(deployment_name)s, id, %(user_id)s
            FROM releases
            WHERE name = %(deployment_release)s
            AND user_id = %(user_id)s
        """
        return self._sql.execute(query, {'deployment_name': deployment['name'], 'user_id': user_id, 'deployment_release': deployment['release']})

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

    def getResults(self, uri):
        query = """
            SELECT d.user_id, r.*
            FROM
            (
                SELECT deployment_id, id AS 'execution_id', 'basic' AS 'mode', engine, public
                FROM deployments_basic
                WHERE uri = %(uri)s
                UNION
                SELECT deployment_id, id AS 'execution_id', 'pro' AS 'mode', engine, public
                FROM deployments_pro
                WHERE uri = %(uri)s
            ) r
            JOIN deployments d ON d.id = r.deployment_id
        """
        return self._sql.execute(query, {'uri': uri})

    def removeRelease(self, release_id):
        query = """
            UPDATE deployments 
            SET release_id = NULL 
            WHERE release_id = %s
        """
        return self._sql.execute(query, (release_id))
