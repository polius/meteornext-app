class Executions_Scheduled:
    def __init__(self, sql):
        self._sql = sql

    def get(self):
        query = """
            SELECT es.execution_id, e.environment_id, e.mode, e.databases, e.queries, e.code, e.method, e.url, e.uri, e.user_id, u.username, u.coins AS 'user_coins', u.group_id, e.deployment_id, d.name AS 'deployment_name', g.deployments_coins, es.schedule_type, es.schedule_value, es.schedule_rules
            FROM executions_scheduled es
            JOIN executions e ON e.id = es.execution_id
            JOIN deployments d ON d.id = e.deployment_id
            JOIN users u ON u.id = e.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE e.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
        """
        return self._sql.execute(query)

    def post(self, execution_id, schedule_type, schedule_value, schedule_rules=None):
        query = """
            INSERT INTO executions_scheduled (execution_id, schedule_type, schedule_value, schedule_rules)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                schedule_type = VALUES(schedule_type),
                schedule_value = VALUES(schedule_value),
                schedule_rules = VALUES(schedule_rules);
        """
        self._sql.execute(query, (execution_id, schedule_type, schedule_value, schedule_rules))

    def delete(self, execution_id):
        query = """
            DELETE FROM executions_scheduled
            WHERE execution_id = %s
        """
        self._sql.execute(query, (execution_id))

    def exists(self, execution_id):
        # Check scheduled executions
        query = """
            SELECT EXISTS(
                SELECT e2.*
                FROM executions e1
                JOIN executions e2 ON e2.deployment_id = e1.deployment_id
                WHERE e1.id = %(execution_id)s
                AND e2.id != %(execution_id)s
                AND e2.status = 'SCHEDULED'
            ) AS 'exist'
        """
        check1 = int(self._sql.execute(query, {"execution_id": execution_id})[0]['exist']) == 1

        # Check recurring scheduled executions
        query = """
            SELECT EXISTS(
                SELECT *
                FROM executions e1
                JOIN executions e2 ON e2.deployment_id = e1.deployment_id
                JOIN executions_scheduled es ON es.execution_id = e2.id
                WHERE e1.id = %(execution_id)s
                AND es.execution_id != %(execution_id)s
            ) AS 'exist'
        """
        check2 = int(self._sql.execute(query, {"execution_id": execution_id})[0]['exist']) == 1

        # Return check
        return check1 and check2
