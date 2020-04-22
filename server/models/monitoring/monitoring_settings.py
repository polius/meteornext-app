class Monitoring_Settings:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id):
        query = "SELECT * FROM monitoring_settings WHERE group_id = %s"
        return self._sql.execute(query, (group_id))

    def put(self, user, data):
        query = """
            INSERT INTO monitoring_settings (`group_id`, `name`, `value`, `updated_by`) 
            VALUES (%s, 'interval', %s, %s), (%s, 'align', %s, %s)
            ON DUPLICATE KEY UPDATE 
                `name` = VALUES(`name`),
                `value` = VALUES(`value`)
        """
        return self._sql.execute(query, (user['group_id'], data['interval'], user['id'], user['group_id'], data['align'], user['id']))