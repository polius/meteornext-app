from datetime import datetime

class Settings:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def get(self, setting_name=None):
        if setting_name:
            query = "SELECT value FROM settings WHERE name = %s"
            return self._sql.execute(query, (setting_name.upper()))[0]['value']
        else:
            query = "SELECT name, value FROM settings"
            return self._sql.execute(query)

    def post(self, user_id, setting):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            UPDATE `settings`
            SET
                `value` = %s,
                `updated_by` = %s,
                `updated_at` = %s
            WHERE `name` = %s
        """
        self._sql.execute(query, (setting['value'], user_id, now, setting['name']))

    def get_license_usage(self):
        query = """
            SELECT u.username, COUNT(s.id) AS 'servers', IF(%(resources)s = -1, 0, COUNT(s.id) > %(resources)s) AS 'exceeded', %(resources)s AS 'resources'
            FROM users u
            JOIN `groups` g ON g.id = u.group_id
            JOIN servers s ON s.group_id = g.id
            WHERE (s.shared = 1 OR s.owner_id = u.id)
            GROUP BY u.id
            ORDER BY COUNT(s.id) DESC;
        """
        return self._sql.execute(query, {"resources": self._license.get_resources()})
