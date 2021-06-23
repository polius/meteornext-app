class Deployments_Finished:
    def __init__(self, sql):
        self._sql = sql

    def get(self):
        query = """
            SELECT e.id, e.mode, d.name, e.status, e.user_id
            FROM deployments_finished f
            JOIN executions e ON e.id = f.execution_id AND e.status IN ('SUCCESS','WARNING','FAILED','STOPPED') 
            JOIN deployments d ON d.id = e.deployment_id
        """
        return self._sql.execute(query)

    def post(self, execution_id):
        self._sql.execute("INSERT INTO deployments_finished (execution_id) VALUES (%s)", (execution_id))

    def delete(self, execution_id):
        self._sql.execute("DELETE FROM deployments_finished WHERE execution_id = %s", (execution_id))
