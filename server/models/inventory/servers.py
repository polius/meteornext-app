from datetime import datetime

class Servers:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id, group_id, server_id=None):
        if server_id is None:
            query = """
                SELECT 
                    s.id, s.name, s.group_id, s.region_id, s.engine, s.version, s.hostname, s.port, s.username, s.password, s.`ssl`, IF(s.ssl_client_key IS NULL, NULL, '<ssl_client_key>') AS 'ssl_client_key', IF(s.ssl_client_certificate IS NULL, NULL, '<ssl_client_certificate>') AS 'ssl_client_certificate', IF(s.ssl_ca_certificate IS NULL, NULL, '<ssl_ca_certificate>') AS 'ssl_ca_certificate', s.ssl_verify_ca, s.`usage`, s.shared, s.owner_id, s.created_by, s.created_at, 
                    r.name AS 'region', r.shared AS 'region_shared'
                FROM servers s
                LEFT JOIN regions r ON r.id = s.region_id
                WHERE s.group_id = %s
                AND (s.shared = 1 OR s.owner_id = %s)
                ORDER BY `name`
            """
            return self._sql.execute(query, (group_id, user_id))
        else:
            query = """
                SELECT 
                    s.id, s.name, s.group_id, s.region_id, s.engine, s.version, s.hostname, s.port, s.username, s.password, s.`ssl`, s.ssl_client_key, s.ssl_client_certificate, s.ssl_ca_certificate, s.ssl_verify_ca, s.`usage`, s.shared, s.owner_id, s.created_by, s.created_at, 
                    r.name AS 'region', r.shared AS 'region_shared'
                FROM servers s
                LEFT JOIN regions r ON r.id = s.region_id
                WHERE s.group_id = %s
                AND (s.shared = 1 OR s.owner_id = %s)
                AND s.id = %s
            """
            return self._sql.execute(query, (group_id, user_id, server_id))

    def post(self, user_id, group_id, server):
        query = """
            INSERT INTO servers (name, group_id, region_id, engine, version, hostname, port, username, password, `ssl`, `ssl_client_key`, `ssl_client_certificate`, `ssl_ca_certificate`, `ssl_verify_ca`, `usage`, shared, owner_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s)
        """
        self._sql.execute(query, (server['name'], group_id, server['region_id'], server['engine'], server['version'], server['hostname'], server['port'], server['username'], server['password'], server['ssl'], server['ssl_client_key'], server['ssl_client_certificate'], server['ssl_ca_certificate'], server['ssl_verify_ca'], server['usage'], server['shared'], server['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group_id, server):
        if 'D' not in server['usage']:
            query = """
                DELETE FROM environment_servers
                WHERE server_id = %s
            """
            self._sql.execute(query, (server['id']))
        if 'C' not in server['usage']:
            query = """
                DELETE FROM client_servers
                WHERE server_id = %s
            """
            self._sql.execute(query, (server['id']))
        query = """
            UPDATE servers
            SET `name` = %s,
                `group_id` = %s,
                `region_id` = %s,
                `engine` = %s,
                `version` = %s,
                `hostname` = %s,
                `port` = %s,
                `username` = %s,
                `password` = %s,
                `ssl` = %s,
                `ssl_client_key` = IF(%s = '<ssl_client_key>', `ssl_client_key`, %s),
                `ssl_client_certificate` = IF(%s = '<ssl_client_certificate>', `ssl_client_certificate`, %s),
                `ssl_ca_certificate` = IF(%s = '<ssl_ca_certificate>', `ssl_ca_certificate`, %s),
                `ssl_verify_ca` = %s,
                `usage` = %s,
                `shared` = %s,
                `owner_id` = IF(%s = 1, NULL, %s),
                `updated_by` = %s,
                `updated_at` = %s
            WHERE `id` = %s
        """
        self._sql.execute(query, (server['name'], group_id, server['region_id'], server['engine'], server['version'], server['hostname'], server['port'], server['username'], server['password'], server['ssl'], server['ssl_client_key'], server['ssl_client_key'], server['ssl_client_certificate'], server['ssl_client_certificate'], server['ssl_ca_certificate'], server['ssl_ca_certificate'], server['ssl_verify_ca'], server['usage'], server['shared'], server['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), server['id']))

    def delete(self, user_id, group_id, server_id):
        # Delete from 'monitoring'
        query = """
            DELETE m 
            FROM monitoring m 
            JOIN servers s ON s.id = m.server_id AND s.id = %s
            WHERE s.group_id = %s
            AND (s.shared = 1 OR s.owner_id = %s)
        """
        self._sql.execute(query, (server_id, group_id, user_id))
        # Delete from 'monitoring_servers'
        query = """
            DELETE ms
            FROM monitoring_servers ms 
            JOIN servers s ON s.id = ms.server_id AND s.id = %s
            WHERE s.group_id = %s
            AND (s.shared = 1 OR s.owner_id = %s)
        """
        self._sql.execute(query, (server_id, group_id, user_id))
        # Delete from 'monitoring_queries'
        query = """
            DELETE mq
            FROM monitoring_queries mq
            JOIN servers s ON s.id = mq.server_id AND s.id = %s
            WHERE s.group_id = %s
            AND (s.shared = 1 OR s.owner_id = %s)
        """
        self._sql.execute(query, (server_id, group_id, user_id))

        # Delete from 'environment_servers'
        query = """
            DELETE es
            FROM environment_servers es
            JOIN servers s ON s.id = es.server_id AND s.id = %s
            WHERE s.group_id = %s
            AND (s.shared = 1 OR s.owner_id = %s)
        """
        self._sql.execute(query, (server_id, group_id, user_id))

        # Delete from 'client_servers'
        query = """
            DELETE cs
            FROM client_servers cs
            JOIN servers s ON s.id = cs.server_id AND s.id = %s
            WHERE s.group_id = %s
            AND (s.shared = 1 OR s.owner_id = %s)
        """
        self._sql.execute(query, (server_id, group_id, user_id))

        # Delete from 'servers'
        query = """
            DELETE s
            FROM servers s
            WHERE s.id = %s
            AND s.group_id = %s
            AND (s.shared = 1 OR s.owner_id = %s)
        """
        self._sql.execute(query, (server_id, group_id, user_id))

    def exist(self, user_id, group_id, server):
        if 'id' in server:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM servers
                    WHERE name = %s
                    AND group_id = %s
                    AND (
                        (shared = 1 AND shared = %s) OR (shared = 0 AND shared = %s AND owner_id = %s)
                    )
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (server['name'], group_id, server['shared'], server['shared'], user_id, server['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM servers
                    WHERE name = %s
                    AND group_id = %s
                    AND (
                        (shared = 1 AND shared = %s) OR (shared = 0 AND shared = %s AND owner_id = %s)
                    )
                ) AS exist
            """
            return self._sql.execute(query, (server['name'], group_id, server['shared'], server['shared'], user_id))[0]['exist'] == 1

    def exist_in_environment(self, user_id, group_id, server_id):
        query = """
            SELECT EXISTS (
                SELECT *
                FROM environment_servers es
                JOIN environments e ON e.id = es.environment_id
                JOIN servers s ON s.id = es.server_id AND s.id = %s AND s.group_id = %s
                WHERE (s.shared = 1 OR s.owner_id = %s)
            ) AS exist
        """
        return self._sql.execute(query, (server_id, group_id, user_id))[0]['exist'] == 1

    def exist_in_client(self, user_id, group_id, server_id):
        query = """
            SELECT EXISTS (
                SELECT *
                FROM client_servers cs
                JOIN servers s ON s.id = cs.server_id AND s.id = %s AND s.group_id = %s
                WHERE (s.shared = 1 OR s.owner_id = %s)
            ) AS exist
        """
        return self._sql.execute(query, (server_id, group_id, user_id))[0]['exist'] == 1

    def get_by_environment(self, user_id, group_id, environment_id):
        query = """
            SELECT s.*
            FROM servers s
            JOIN environment_servers es ON es.server_id = s.id
            JOIN environments e ON e.id = es.environment_id AND e.group_id = %s AND e.id = %s
            WHERE (s.shared = 1 OR s.owner_id = %s)
        """
        return self._sql.execute(query, (group_id, environment_id, user_id))
