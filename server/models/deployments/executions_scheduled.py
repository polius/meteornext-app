class Executions_Scheduled:
    def __init__(self, sql):
        self._sql = sql

    def post(self, execution_id, schedule_type, schedule_rules=None):
        query = """
            INSERT INTO executions_scheduled (execution_id, schedule_type, schedule_rules)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                schedule_type = VALUES(schedule_type),
                schedule_rules = VALUES(schedule_rules);
        """
        self._sql.execute(query, (execution_id, schedule_type, schedule_rules))
