class Deployments_Pinned:
    def __init__(self, sql):
        self._sql = sql

    def post(self, user_id, deployment_id):
        self._sql.execute("INSERT IGNORE INTO deployments_pinned (user_id, deployment_id) VALUES (%s, %s)", (user_id, deployment_id))

    def delete(self, user_id, deployment_id):
        self._sql.execute("DELETE FROM deployments_pinned WHERE user_id = %s AND deployment_id = %s", (user_id, deployment_id))
