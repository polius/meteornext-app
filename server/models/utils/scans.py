from datetime import datetime

class Scans:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id, scan_id):
        query = """
            SELECT *
            FROM imports_scans
            WHERE user_id = %s
            AND id = %s
        """
        return self._sql.execute(query, (user_id, scan_id))

    def post(self, user, data):
        query = """
            INSERT INTO `imports_scans` (`mode`, `cloud_id`, `bucket`, `source`, `size`, `status`, `updated`, `uri`, `user_id`)
            VALUES (%s, %s, %s, %s, %s, 'IN PROGRESS', %s, %s, %s)
        """
        return self._sql.execute(query, (data['mode'], data['cloud_id'] if 'cloud_id' in data else None, data['bucket'] if 'bucket' in data else None, data['source'], data['metadata']['size'], self.__utcnow(), data['uri'], user['id']))

    def put_readed(self, scan_id):
        query = """
            UPDATE `imports_scans`
            SET `readed` = %s
            WHERE id = %s
        """
        self._sql.execute(query, (self.__utcnow(), scan_id))

    def put_status(self, scan_id, status):
        query = """
            UPDATE `imports_scans`
            SET `status` = %s
            WHERE id = %s
        """
        self._sql.execute(query, (status, scan_id))

    def __utcnow(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
