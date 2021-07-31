from datetime import datetime

class Scans:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id, scan_id):
        query = """
            SELECT *
            FROM restore_scans
            WHERE user_id = %s
            AND id = %s
        """
        return self._sql.execute(query, (user_id, scan_id))

    def post(self, user, data):
        query = """
            INSERT INTO `restore_scans` (`mode`, `cloud_id`, `source`, `size`, `status`, `updated`, `uri`, `user_id`)
            VALUES (%s, %s, %s, %s, 'IN PROGRESS', %s, %s, %s)
        """
        return self._sql.execute(query, (data['mode'], data['cloud_id'], data['source'], data['metadata']['size'], self.__utcnow(), data['uri'], user['id']))

    def __utcnow(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
