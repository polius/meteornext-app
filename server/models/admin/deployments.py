class Deployments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, dfilter=None, dsort=None):
        user = name = release = mode = status = date_from = date_to = ''
        args = {}
        sort_column = 'd.created'
        sort_order = 'DESC'
        if dfilter is not None:
            matching = {
                'equal':        { 'operator': '=', 'args': '{}' },
                'not_equal':    { 'operator': '!=', 'args': '{}' },
                'starts':       { 'operator': 'LIKE', 'args': '{}%' },
                'not_starts':   { 'operator': 'NOT LIKE', 'args': '{}%' },
                'contains':     { 'operator': 'LIKE', 'args': '%{}%' },
                'not_contains': { 'operator': 'NOT LIKE', 'args': '%{}%' }
            }
            if 'user' in dfilter and dfilter['user'] is not None:
                user = 'AND u.username = %(user)s'
                args['user'] = dfilter['user']
            if 'name' in dfilter and len(dfilter['name']) > 0 and 'nameFilter' in dfilter and dfilter['nameFilter'] in matching:
                name = f"AND d.name {matching[dfilter['nameFilter']]['operator']} %(name)s"
                args['name'] = matching[dfilter['nameFilter']]['args'].format(dfilter['name'])
            if 'release' in dfilter and len(dfilter['release']) > 0 and 'releaseFilter' in dfilter and dfilter['releaseFilter'] in matching:
                release = f"AND r.name {matching[dfilter['releaseFilter']]['operator']} %(release)s"
                args['release'] = matching[dfilter['releaseFilter']]['args'].format(dfilter['release'])
            if 'mode' in dfilter and dfilter['mode'] is not None:
                mode = 'AND d.mode = %(mode)s'
                args['mode'] = dfilter['mode']
            if 'status' in dfilter and dfilter['status'] is not None:
                status = 'AND d.status = %(status)s'
                args['status'] = dfilter['status']
            if 'dateFrom' in dfilter and len(dfilter['dateFrom']) > 0:
                date_from = 'AND d.created >= %(date_from)s'
                args['date_from'] = dfilter['dateFrom']
            if 'dateTo' in dfilter and len(dfilter['dateTo']) > 0:
                date_to = 'AND d.created <= %(date_to)s'
                args['date_to'] = dfilter['dateTo']

        if dsort is not None:
            sort_column = dsort['column']
            sort_order = 'DESC' if dsort['desc'] else 'ASC'

        query = """
            SELECT *, e.name AS 'environment', r.name AS 'release'
            FROM
            (
                (
                    SELECT d.id, db.id AS 'execution_id', u.username, d.name, d.release_id, db.environment_id, 'BASIC' AS 'mode', db.method, db.status, db.created, db.scheduled, db.started, db.ended, CONCAT(TIMEDIFF(db.ended, db.started)) AS 'overall'
                    FROM deployments_basic db
                    JOIN deployments d ON d.id = db.deployment_id
                    JOIN users u ON u.id = d.user_id {0}
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
                    JOIN users u ON u.id = d.user_id {0}
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
            WHERE 1=1
            {1} {2} {3} {4} {5} {6}
            ORDER BY {7} {8}
            LIMIT 1000
        """.format(user, name, release, mode, status, date_from, date_to, sort_column, sort_order)
        return self._sql.execute(query, args)

    def get_users_list(self):
        query = """
            SELECT u.username AS 'user', g.name AS 'group'
            FROM users u
            JOIN groups g ON g.id = u.group_id
            ORDER BY u.username
        """
        return self._sql.execute(query)

    def put_name(self, user_id, deployment):
        query = """
            UPDATE deployments
            SET name = %s
            WHERE id = %s
            AND user_id = %s
        """
        self._sql.execute(query, (deployment['name'], deployment['id'], user_id))

    def put_release(self, user_id, deployment):
        query = """
            UPDATE deployments, releases
            SET deployments.release_id = releases.id
            WHERE deployments.id = %s
            AND deployments.user_id = %s
            AND releases.name = %s
            AND releases.user_id = %s
        """
        self._sql.execute(query, (deployment['id'], user_id, deployment['release'], user_id))