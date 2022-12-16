from datetime import datetime

class Deployments_Shared:
    def __init__(self, sql):
        self._sql = sql

    ###################
    # SHARED WITH YOU #
    ###################
    def get_you(self, user_id=None, dfilter=None, dsort=None):
        name = release = environment = mode = method = status = owner = created_from = created_to = started_from = started_to = ended_from = ended_to = ''
        args = { 'user_id': user_id }
        if dfilter is not None:
            if 'name' in dfilter and len(dfilter['name']) > 0:
                name = "AND d.name = %(name)s"
                args['name'] = dfilter['name']
            if 'release' in dfilter and len(dfilter['release']) > 0:
                release = "AND r.name = %(release)s"
                args['release'] = dfilter['release']
            if 'environment' in dfilter and len(dfilter['environment']) > 0:
                environment = "AND env.name = %(environment)s"
                args['environment'] = dfilter['environment']
            if 'mode' in dfilter and dfilter['mode'] is not None and len(dfilter['mode']) > 0:
                mode = 'AND e.mode IN (%s)' % ','.join([f"%(mode{i})s" for i in range(len(dfilter['mode']))])
                for i,v in enumerate(dfilter['mode']):
                    args[f'mode{i}'] = v
            if 'method' in dfilter and dfilter['method'] is not None and len(dfilter['method']) > 0:
                method = 'AND e.method IN (%s)' % ','.join([f"%(method{i})s" for i in range(len(dfilter['method']))])
                for i,v in enumerate(dfilter['method']):
                    args[f'method{i}'] = v
            if 'status' in dfilter and dfilter['status'] is not None and len(dfilter['status']) > 0:
                status = 'AND e.status IN (%s)' % ','.join([f"%(status{i})s" for i in range(len(dfilter['status']))])
                for i,v in enumerate(dfilter['status']):
                    args[f'status{i}'] = v
            if 'owner' in dfilter and len(dfilter['owner']) > 0:
                owner = "AND u.username = %(owner)s"
                args['owner'] = dfilter['owner']
            if 'createdFrom' in dfilter and len(dfilter['createdFrom']) > 0:
                created_from = 'AND e.created >= %(created_from)s'
                args['created_from'] = dfilter['createdFrom']
            if 'createdTo' in dfilter and len(dfilter['createdTo']) > 0:
                created_to = 'AND e.created <= %(created_to)s'
                args['created_to'] = dfilter['createdTo']
            if 'startedFrom' in dfilter and len(dfilter['startedFrom']) > 0:
                started_from = 'AND e.started >= %(started_from)s'
                args['started_from'] = dfilter['startedFrom']
            if 'startedTo' in dfilter and len(dfilter['startedTo']) > 0:
                started_to = 'AND e.started <= %(started_to)s'
                args['started_to'] = dfilter['startedTo']
            if 'endedFrom' in dfilter and len(dfilter['endedFrom']) > 0:
                ended_from = 'AND e.ended >= %(ended_from)s'
                args['ended_from'] = dfilter['endedFrom']
            if 'endedTo' in dfilter and len(dfilter['endedTo']) > 0:
                ended_to = 'AND e.ended <= %(ended_to)s'
                args['ended_to'] = dfilter['endedTo']

        query = """
            SELECT d.id, e.id AS 'execution_id', e.uri, d.name, env.name AS 'environment', r.name AS 'release', e.mode, e.method, e.status, q.queue, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall', ds.is_pinned, u.username AS 'owner'
            FROM executions e
            JOIN deployments d ON d.id = e.deployment_id
            JOIN deployments_shared ds ON ds.user_id = %(user_id)s AND ds.deployment_id = d.id
            JOIN users u ON u.id = d.user_id
            JOIN `groups` g ON g.id = u.group_id
            LEFT JOIN environments env ON env.id = e.environment_id
            LEFT JOIN releases r ON r.id = d.release_id
            LEFT JOIN
            (
                SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                FROM executions
                JOIN (SELECT @cnt := 0) t
                WHERE status = 'QUEUED'
            ) q ON q.deployment_id = d.id
            WHERE e.id IN (
                SELECT MAX(id)
                FROM executions e2
                WHERE e2.deployment_id = e.deployment_id
            )
            AND d.shared = 1
            {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} {12}
            ORDER BY ds.id DESC
        """.format(name, release, environment, mode, method, status, owner, created_from, created_to, started_from, started_to, ended_from, ended_to)
        return self._sql.execute(query, args)

    def check_uri(self, user_id, uri):
        query = """
            SELECT d.user_id, ds.deployment_id IS NOT NULL AS 'already_added'
            FROM executions e
            JOIN deployments d ON d.id = e.deployment_id AND d.shared = 1
            LEFT JOIN deployments_shared ds ON ds.deployment_id = d.id AND ds.user_id = %s
            WHERE e.uri = %s
        """
        return self._sql.execute(query, (user_id, uri))

    def post_you(self, user_id, uri):
        query = """
            INSERT IGNORE INTO deployments_shared (user_id, deployment_id, created)
            SELECT %s, d.id, %s
            FROM deployments d
            JOIN executions e ON e.deployment_id = d.id AND e.uri = %s
            AND d.shared = 1
            LIMIT 1
        """
        self._sql.execute(query, (user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), uri))

    def delete_you(self, user_id, deployment_id):
        query = """
            DELETE FROM deployments_shared
            WHERE user_id = %s
            AND deployment_id = %s
        """
        self._sql.execute(query, (user_id, deployment_id))

    def pin_you(self, user_id, deployment_id, value):
        query = """
            UPDATE deployments_shared
            SET is_pinned = %s
            WHERE user_id = %s
            AND deployment_id = %s
        """
        self._sql.execute(query, (value, user_id, deployment_id))

    ######################
    # SHARED WITH OTHERS #
    ######################
    def get_others(self, user_id=None, dfilter=None, dsort=None):
        name = release = mode = method = status = created_from = created_to = started_from = started_to = ended_from = ended_to = ''
        args = { 'user_id': user_id }
        if dfilter is not None:
            if 'name' in dfilter and len(dfilter['name']) > 0:
                name = "AND d.name = %(name)s"
                args['name'] = dfilter['name']
            if 'release' in dfilter and len(dfilter['release']) > 0:
                release = "AND r.name = %(release)s"
                args['release'] = dfilter['release']
            if 'mode' in dfilter and dfilter['mode'] is not None and len(dfilter['mode']) > 0:
                mode = 'AND e.mode IN (%s)' % ','.join([f"%(mode{i})s" for i in range(len(dfilter['mode']))])
                for i,v in enumerate(dfilter['mode']):
                    args[f'mode{i}'] = v
            if 'method' in dfilter and dfilter['method'] is not None and len(dfilter['method']) > 0:
                method = 'AND e.method IN (%s)' % ','.join([f"%(method{i})s" for i in range(len(dfilter['method']))])
                for i,v in enumerate(dfilter['method']):
                    args[f'method{i}'] = v
            if 'status' in dfilter and dfilter['status'] is not None and len(dfilter['status']) > 0:
                status = 'AND e.status IN (%s)' % ','.join([f"%(status{i})s" for i in range(len(dfilter['status']))])
                for i,v in enumerate(dfilter['status']):
                    args[f'status{i}'] = v
            if 'createdFrom' in dfilter and len(dfilter['createdFrom']) > 0:
                created_from = 'AND e.created >= %(created_from)s'
                args['created_from'] = dfilter['createdFrom']
            if 'createdTo' in dfilter and len(dfilter['createdTo']) > 0:
                created_to = 'AND e.created <= %(created_to)s'
                args['created_to'] = dfilter['createdTo']
            if 'startedFrom' in dfilter and len(dfilter['startedFrom']) > 0:
                started_from = 'AND e.started >= %(started_from)s'
                args['started_from'] = dfilter['startedFrom']
            if 'startedTo' in dfilter and len(dfilter['startedTo']) > 0:
                started_to = 'AND e.started <= %(started_to)s'
                args['started_to'] = dfilter['startedTo']
            if 'endedFrom' in dfilter and len(dfilter['endedFrom']) > 0:
                ended_from = 'AND e.ended >= %(ended_from)s'
                args['ended_from'] = dfilter['endedFrom']
            if 'endedTo' in dfilter and len(dfilter['endedTo']) > 0:
                ended_to = 'AND e.ended <= %(ended_to)s'
                args['ended_to'] = dfilter['endedTo']

        query = """
            SELECT d.id, e.id AS 'execution_id', e.uri, d.name, env.name AS 'environment', r.name AS 'release', e.mode, e.method, e.status, q.queue, e.created, e.scheduled, e.started, e.ended, CONCAT(TIMEDIFF(e.ended, e.started)) AS 'overall'
            FROM executions e
            JOIN deployments d ON d.id = e.deployment_id AND d.user_id = %(user_id)s
            JOIN users u ON u.id = d.user_id
            JOIN `groups` g ON g.id = u.group_id
            LEFT JOIN environments env ON env.id = e.environment_id
            LEFT JOIN releases r ON r.id = d.release_id
            LEFT JOIN
            (
                SELECT (@cnt := @cnt + 1) AS queue, deployment_id
                FROM executions
                JOIN (SELECT @cnt := 0) t
                WHERE status = 'QUEUED'
            ) q ON q.deployment_id = d.id
            WHERE e.id IN (
                SELECT MAX(id)
                FROM executions e2
                WHERE e2.deployment_id = e.deployment_id
            )
            AND d.shared = 1
            {0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10}
            ORDER BY created DESC, id DESC
        """.format(name, release, mode, method, status, created_from, created_to, started_from, started_to, ended_from, ended_to)
        return self._sql.execute(query, args)

    def delete_others(self, user_id, deployment_id):
        query = """
            DELETE ds 
            FROM deployments_shared ds
            JOIN deployments d ON d.id = ds.deployment_id AND d.user_id = %s AND d.id = %s
        """
        self._sql.execute(query, (user_id, deployment_id))

        query = """
            UPDATE deployments
            SET shared = 0
            WHERE user_id = %s
            AND id = %s
        """
        self._sql.execute(query, (user_id, deployment_id))
