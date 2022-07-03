from datetime import datetime

class Monitoring:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def get(self, user, server_id):
        query = """
            SELECT ms.*, s.name, s.hostname, t.id IS NOT NULL AS 'active', r.name AS 'region', r.shared AS 'region_shared'
            FROM monitoring_servers ms
            JOIN servers s ON s.id = ms.server_id AND s.id = %(server_id)s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %(group_id)s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = %(user_id)s)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            WHERE (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%M%%'
            ORDER BY s.id
        """
        return self._sql.execute(query, {"server_id": server_id, "group_id": user['group_id'], "user_id": user['id'], "license": self._license.get_resources()})

    def get_monitoring(self, user):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', t.id IS NOT NULL AS 'server_active', r.id AS 'region_id', r.name AS 'region_name', r.shared AS 'region_shared', s.hostname, (m.monitor_enabled IS NOT NULL AND m.monitor_enabled = 1) AS 'selected', ms.available, ms.summary, ms.error, ms.updated
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %(group_id)s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = %(user_id)s)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            LEFT JOIN monitoring m ON m.server_id = s.id AND m.user_id = %(user_id)s
            LEFT JOIN monitoring_servers ms ON ms.server_id = m.server_id
            WHERE (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%M%%'
            ORDER BY r.name, s.name
        """
        return self._sql.execute(query, {"group_id": user['group_id'], "user_id": user['id'], "license": self._license.get_resources()})

    def get_parameters(self, user):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', t.id IS NOT NULL AS 'server_active', r.id AS 'region_id', r.name AS 'region_name', r.shared AS 'region_shared', s.hostname, (m.parameters_enabled IS NOT NULL AND m.parameters_enabled = 1) AS 'selected', ms.available, ms.parameters, ms.updated
            FROM servers s
			JOIN regions r ON r.id = s.region_id AND r.group_id = %(group_id)s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = %(user_id)s)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            LEFT JOIN monitoring m ON m.server_id = s.id AND m.user_id = %(user_id)s
            LEFT JOIN monitoring_servers ms ON ms.server_id = m.server_id
            WHERE (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%M%%'
            ORDER BY r.name, s.name
        """
        return self._sql.execute(query, {"group_id": user['group_id'], "user_id": user['id'], "license": self._license.get_resources()})

    def get_processlist(self, user):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', t.id IS NOT NULL AS 'server_active', r.id AS 'region_id', r.name AS 'region_name', r.shared AS 'region_shared', s.hostname, (m.processlist_enabled IS NOT NULL AND m.processlist_enabled = 1) AS 'selected', ms.available, ms.processlist, ms.updated
            FROM servers s
			JOIN regions r ON r.id = s.region_id AND r.group_id = %(group_id)s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = %(user_id)s)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            LEFT JOIN monitoring m ON m.server_id = s.id AND m.user_id = %(user_id)s
            LEFT JOIN monitoring_servers ms ON ms.server_id = m.server_id
            WHERE (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%M%%'
            ORDER BY r.name, s.name
        """
        return self._sql.execute(query, {"group_id": user['group_id'], "user_id": user['id'], "license": self._license.get_resources()})

    def get_queries(self, user):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', s.shared AS 'server_shared', s.secured AS 'server_secured', t.id IS NOT NULL AS 'server_active', r.id AS 'region_id', r.name AS 'region_name', r.shared AS 'region_shared', s.hostname, (m.queries_enabled IS NOT NULL AND m.queries_enabled = 1) AS 'selected'
            FROM servers s
			JOIN regions r ON r.id = s.region_id AND r.group_id = %(group_id)s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = %(user_id)s)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            LEFT JOIN monitoring m ON m.server_id = s.id AND m.user_id = %(user_id)s
            LEFT JOIN monitoring_servers ms ON ms.server_id = m.server_id
            WHERE (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%M%%'
            ORDER BY r.name, s.name
        """
        return self._sql.execute(query, {"group_id": user['group_id'], "user_id": user['id'], "license": self._license.get_resources()})

    def get_events(self, user):
        query = """
            SELECT me.id, s.name AS 'server', me.event, me.data, me.time 
            FROM monitoring_events me
            JOIN monitoring m ON m.server_id = me.server_id AND m.user_id = %s
            JOIN servers s ON s.id = m.server_id
            ORDER BY me.id DESC
        """
        return self._sql.execute(query, (user['id']))

    def put_monitor(self, user, data):
        if len(data) == 0:
            query = """
                UPDATE monitoring
                SET monitor_enabled = 0
                WHERE user_id = %s
            """
            self._sql.execute(query, (user['id']))
        else:
            query = """
                UPDATE monitoring
                SET monitor_enabled = 0
                WHERE user_id = {}
                AND server_id NOT IN ({})
            """.format(user['id'], ','.join(['%s'] * len(data)))
            self._sql.execute(query, (data))
            
            for i in data:
                query = """
                    INSERT INTO monitoring (user_id, server_id, monitor_enabled, `date`)
                    SELECT %s, s.id, 1, %s
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id AND r.group_id = %s
                    WHERE s.id = %s
                    ON DUPLICATE KEY UPDATE monitor_enabled = 1
                """
                self._sql.execute(query, (user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['group_id'], i))

    def put_parameters(self, user, data):
        if len(data) == 0:
            query = """
                UPDATE monitoring
                SET parameters_enabled = 0
                WHERE user_id = %s
            """
            self._sql.execute(query, (user['id']))
        else:
            query = """
                UPDATE monitoring
                SET parameters_enabled = 0
                WHERE user_id = {}
                AND server_id NOT IN ({})
            """.format(user['id'], ','.join(['%s'] * len(data)))
            self._sql.execute(query, (data))
            
            for i in data:
                query = """
                    INSERT INTO monitoring (user_id, server_id, parameters_enabled, `date`)
                    SELECT %s, s.id, 1, %s
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id AND r.group_id = %s
                    WHERE s.id = %s
                    ON DUPLICATE KEY UPDATE parameters_enabled = 1
                """
                self._sql.execute(query, (user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['group_id'], i))

    def put_processlist(self, user, data):
        if len(data) == 0:
            query = """
                UPDATE monitoring
                SET processlist_enabled = 0
                AND processlist_active = 0
                WHERE user_id = %s
            """
            self._sql.execute(query, (user['id']))
        else:
            query = """
                UPDATE monitoring
                SET processlist_enabled = 0,
                    processlist_active = 0
                WHERE user_id = {}
                AND server_id NOT IN ({})
            """.format(user['id'], ','.join(['%s'] * len(data)))
            self._sql.execute(query, (data))
            
            for i in data:
                query = """
                    INSERT INTO monitoring (user_id, server_id, processlist_enabled, processlist_active, `date`)
                    SELECT %s, s.id, 1, 1, %s
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id AND r.group_id = %s
                    WHERE s.id = %s
                    ON DUPLICATE KEY UPDATE processlist_enabled = 1, processlist_active = 1
                """
                self._sql.execute(query, (user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['group_id'], i))

    def put_queries(self, user, data):
        if len(data) == 0:
            query = """
                UPDATE monitoring
                SET queries_enabled = 0
                WHERE user_id = %s
            """
            self._sql.execute(query, (user['id']))
        else:
            query = """
                UPDATE monitoring
                SET queries_enabled = 0
                WHERE user_id = {}
                AND server_id NOT IN ({})
            """.format(user['id'], ','.join(['%s'] * len(data)))
            self._sql.execute(query, (data))
            
            for i in data:
                query = """
                    INSERT INTO monitoring (user_id, server_id, queries_enabled, `date`)
                    SELECT %s, s.id, 1, %s
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id AND r.group_id = %s
                    WHERE s.id = %s
                    ON DUPLICATE KEY UPDATE queries_enabled = 1
                """
                self._sql.execute(query, (user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['group_id'], i))

    def start_processlist(self, user):
        query = """
            UPDATE monitoring
            SET processlist_active = 1
            WHERE user_id = %s
        """
        self._sql.execute(query, (user['id']))

    def stop_processlist(self, user):
        query = """
            UPDATE monitoring
            SET processlist_active = 0
            WHERE user_id = %s
        """
        self._sql.execute(query, (user['id']))
