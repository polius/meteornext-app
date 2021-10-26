from datetime import datetime

class Servers:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, server_id=None, user_id=None):
        if user_id is not None:
            query = """
                SELECT s.id, s.name, s.group_id, g.name AS 'group', s.region_id, s.engine, s.version, s.hostname, s.port, s.username, s.password, s.`ssl`, s.ssl_client_key, s.ssl_client_certificate, s.ssl_ca_certificate, s.ssl_verify_ca, s.usage, s.shared, s.owner_id, u.username AS 'owner', u2.username AS 'created_by', s.created_at, u3.username AS 'updated_by', s.updated_at, r.name AS 'region', r.shared AS 'region_shared'
                FROM servers s
                JOIN users u0 ON u0.id = %(user_id)s
                JOIN groups g ON g.id = s.group_id AND g.id = u0.group_id
                LEFT JOIN regions r ON r.id = s.region_id
                LEFT JOIN users u ON u.id = s.owner_id
                LEFT JOIN users u2 ON u2.id = s.created_by
                LEFT JOIN users u3 ON u3.id = s.updated_by
                WHERE (s.shared = 1 OR s.owner_id = %(user_id)s)
                ORDER BY s.id DESC
            """
            return self._sql.execute(query, {"user_id": user_id})
        elif group_id is not None:
            query = """
                SELECT s.id, s.name, s.group_id, g.name AS 'group', s.region_id, s.engine, s.version, s.hostname, s.port, s.username, s.password, s.`ssl`, s.ssl_client_key, s.ssl_client_certificate, s.ssl_ca_certificate, s.ssl_verify_ca, s.usage, s.shared, s.owner_id, u.username AS 'owner', u2.username AS 'created_by', s.created_at, u3.username AS 'updated_by', s.updated_at, r.name AS 'region', r.shared AS 'region_shared'
                FROM servers s
                LEFT JOIN regions r ON r.id = s.region_id
                LEFT JOIN users u ON u.id = s.owner_id
                LEFT JOIN users u2 ON u2.id = s.created_by
                LEFT JOIN users u3 ON u3.id = s.updated_by
                LEFT JOIN groups g ON g.id = s.group_id
                WHERE s.group_id = %s
                ORDER BY s.id DESC
            """
            return self._sql.execute(query, (group_id))
        elif server_id is not None:
            query = """
                SELECT s.*, r.name AS 'region', r.shared AS 'region_shared', g.name AS 'group', u.username AS 'owner'
                FROM servers s
                LEFT JOIN groups g ON g.id = s.group_id
                LEFT JOIN regions r ON r.id = s.region_id
                LEFT JOIN users u ON u.id = s.owner_id
                WHERE s.id = %s
            """
            return self._sql.execute(query, (server_id))
        else:
            query = """
                SELECT s.id, s.name, s.group_id, g.name AS 'group', s.region_id, s.engine, s.version, s.hostname, s.port, s.username, s.password, s.`ssl`, `ssl_client_key`, `ssl_client_certificate`, `ssl_ca_certificate`, `ssl_verify_ca`, s.usage, s.shared, s.owner_id, u.username AS 'owner', u2.username AS 'created_by', s.created_at, u3.username AS 'updated_by', s.updated_at, r.name AS 'region', r.shared AS 'region_shared'
                FROM servers s
                LEFT JOIN regions r ON r.id = s.region_id
                LEFT JOIN users u ON u.id = s.owner_id
                LEFT JOIN users u2 ON u2.id = s.created_by
                LEFT JOIN users u3 ON u3.id = s.updated_by
                LEFT JOIN groups g ON g.id = s.group_id
                ORDER BY s.id DESC
            """
            return self._sql.execute(query)

    def post(self, user, server):
        query = """
            INSERT INTO servers (name, group_id, region_id, engine, version, hostname, port, username, password, `ssl`, `ssl_client_key`, `ssl_client_certificate`, `ssl_ca_certificate`, `ssl_verify_ca`, `usage`, shared, owner_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s)
        """
        self._sql.execute(query, (server['name'], server['group_id'], server['region_id'], server['engine'], server['version'], server['hostname'], server['port'], server['username'], server['password'], server['ssl'], server['ssl_client_key'], server['ssl_client_certificate'], server['ssl_ca_certificate'], server['ssl_verify_ca'], server['usage'], server['shared'], server['shared'], server['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user, server):
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
        self._sql.execute(query, (server['name'], server['region_id'], server['engine'], server['version'], server['hostname'], server['port'], server['username'], server['password'], server['ssl'], server['ssl_client_key'], server['ssl_client_key'], server['ssl_client_certificate'], server['ssl_client_certificate'], server['ssl_ca_certificate'], server['ssl_ca_certificate'], server['ssl_verify_ca'], server['usage'], server['shared'], server['shared'], server['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), server['id']))

    def delete(self, server_id):
        # Delete from 'monitoring'
        query = """
            DELETE m 
            FROM monitoring m 
            JOIN servers s ON s.id = m.server_id AND s.id = %s
        """
        self._sql.execute(query, (server_id))
        # Delete from 'monitoring_servers'
        query = """
            DELETE ms
            FROM monitoring_servers ms 
            JOIN servers s ON s.id = ms.server_id AND s.id = %s
        """
        self._sql.execute(query, (server_id))
        # Delete from 'monitoring_queries'
        query = """
            DELETE mq
            FROM monitoring_queries mq
            JOIN servers s ON s.id = mq.server_id AND s.id = %s
        """
        self._sql.execute(query, (server_id))

        # Delete from 'environment_servers'
        query = """
            DELETE es
            FROM environment_servers es
            JOIN servers s ON s.id = es.server_id AND s.id = %s
        """
        self._sql.execute(query, (server_id))

        # Delete from 'client_servers'
        query = """
            DELETE cs
            FROM client_servers cs
            JOIN servers s ON s.id = cs.server_id AND s.id = %s
        """
        self._sql.execute(query, (server_id))

        # Delete from 'client_queries'
        query = """
            DELETE cq
            FROM client_queries cq
            JOIN servers s ON s.id = cq.server_id AND s.id = %s
        """
        self._sql.execute(query, (server_id))

        # Delete from 'servers'
        query = """
            DELETE FROM servers
            WHERE id = %s
        """
        self._sql.execute(query, (server_id))

    def exist(self, server):
        if 'id' in server:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM servers
                    WHERE `name` = %s 
                    AND group_id = %s
                    AND (shared = 1 OR owner_id = %s)
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (server['name'], server['group_id'], server['owner_id'], server['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM servers
                    WHERE `name` = %s 
                    AND group_id = %s
                    AND (shared = 1 OR owner_id = %s)
                ) AS exist
            """
            return self._sql.execute(query, (server['name'], server['group_id'], server['owner_id']))[0]['exist'] == 1

    def exist_in_environment(self, server):
        query = """
            SELECT EXISTS (
                SELECT *
                FROM environment_servers es
                JOIN environments e ON e.id = es.environment_id
                JOIN servers s ON s.id = es.server_id AND s.id = %s
            ) AS exist
        """
        return self._sql.execute(query, (server))[0]['exist'] == 1

    def exist_in_client(self, server):
        query = """
            SELECT EXISTS (
                SELECT *
                FROM client_servers cs
                JOIN servers s ON s.id = cs.server_id AND s.id = %s
            ) AS exist
        """
        return self._sql.execute(query, (server))[0]['exist'] == 1
