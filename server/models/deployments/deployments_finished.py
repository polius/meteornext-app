class Deployments_Finished:
    def __init__(self, sql):
        self._sql = sql

    def getBasic(self):
        query = """
            SELECT b.id, d.name, d.user_id, e.name AS 'environment', b.status
            FROM deployments_finished f
            JOIN deployments_basic b ON b.id = f.deployment_id AND f.deployment_mode = 'BASIC' AND b.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            JOIN deployments d ON d.id = b.deployment_id
            LEFT JOIN releases r ON r.id = d.release_id
            JOIN environments e ON e.id = b.environment_id
        """
        return self._sql.execute(query)

    def getPro(self):
        query = """
            SELECT p.id, d.name, d.user_id, e.name AS 'environment', p.status
            FROM deployments_finished f
            JOIN deployments_pro p ON p.id = f.deployment_id AND f.deployment_mode = 'PRO' AND p.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            JOIN deployments d ON d.id = p.deployment_id
            LEFT JOIN releases r ON r.id = d.release_id
            JOIN environments e ON e.id = p.environment_id
        """
        return self._sql.execute(query)

    def post(self, deployment):
        self._sql.execute("INSERT INTO deployments_finished (deployment_mode, deployment_id) VALUES (%s, %s)", (deployment['mode'], deployment['id']))

    def delete(self, deployment):
        self._sql.execute("DELETE FROM deployments_finished WHERE deployment_mode = %s AND deployment_id = %s", (deployment['mode'], deployment['id']))