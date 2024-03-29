class Monitoring_Settings:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user):
        query = """
            SELECT 
                ms.`monitor_align`,
                ms.`monitor_slack_enabled`,
                ms.`monitor_slack_url`,
                ms.`monitor_base_url`,
                ms.`query_execution_time`,
                ms.`query_data_retention`,
                g.`monitoring_interval` AS 'monitor_interval' 
            FROM monitoring_settings ms
            JOIN users u ON u.id = ms.user_id
            JOIN `groups` g ON g.id = u.group_id
            WHERE user_id = %s
        """
        return self._sql.execute(query, (user['id']))

    def put(self, user, data):
        if not data:
            return
        headers = ','.join(data.keys())
        duplicate = ','.join(["{}=%s".format(k, data[k]) for k in data])
        query = """
            INSERT INTO monitoring_settings (user_id,{})
            VALUES ({},{})
            ON DUPLICATE KEY UPDATE {}
        """.format(headers, user['id'], ','.join(['%s'] * len(data.values())), duplicate)
        self._sql.execute(query, (list(data.values())*2))
