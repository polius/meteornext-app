from datetime import datetime

class Servers:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id, group_id, server_id=None):
        if server_id is None:
            query = """
                SELECT s.*, r.name AS 'region' 
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s
                WHERE (s.shared = 1 OR s.owner_id = %s)
            """
            return self._sql.execute(query, (group_id, user_id))
        else:
            query = """
                SELECT s.*, r.name AS 'region' 
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s
                WHERE s.id = %s
            """
            return self._sql.execute(query, (group_id, server_id))

    def post(self, user_id, group_id, server):
        query = """
            INSERT INTO servers (name, region_id, engine, version, hostname, port, username, password, `ssl`, shared, owner_id, created_by, created_at)             
            SELECT %s, id, %s, %s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s
            FROM regions
            WHERE group_id = %s
            AND name = %s
        """
        self._sql.execute(query, (server['name'], server['engine'], server['version'], server['hostname'], server['port'], server['username'], server['password'], server['ssl'], server['shared'], server['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), group_id, server['region']))

    def put(self, user_id, group_id, server):
        query = """
            UPDATE servers
            JOIN regions r ON r.id = servers.region_id AND r.id = %s AND r.group_id = %s
            SET servers.name = %s,
                servers.region_id = (SELECT id FROM regions WHERE group_id = %s AND name = %s),
                servers.engine = %s,
                servers.version = %s,
                servers.hostname = %s,
                servers.port = %s,
                servers.username = %s,
                servers.password = %s,
                servers.`ssl` = %s,
                servers.shared = %s,
                servers.owner_id = IF(%s = 1, NULL, %s),
                servers.updated_by = %s,
                servers.updated_at = %s
            WHERE servers.id = %s
        """
        self._sql.execute(query, (server['region_id'], group_id, server['name'], group_id, server['region'], server['engine'], server['version'], server['hostname'], server['port'], server['username'], server['password'], server['ssl'], server['shared'], server['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), server['id']))

    def delete(self, group_id, server_id):
        # Delete from 'monitoring'
        query = """
            DELETE m 
            FROM monitoring m 
            JOIN servers s ON s.id = m.server_id AND s.id = %s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
        """
        self._sql.execute(query, (server_id, group_id))
        # Delete from 'monitoring_servers'
        query = """
            DELETE ms
            FROM monitoring_servers ms 
            JOIN servers s ON s.id = ms.server_id AND s.id = %s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
        """
        self._sql.execute(query, (server_id, group_id))
        # Delete from 'monitoring_queries'
        query = """
            DELETE mq
            FROM monitoring_queries mq
            JOIN servers s ON s.id = mq.server_id AND s.id = %s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
        """
        self._sql.execute(query, (server_id, group_id))

        # Delete from 'environment_servers'
        query = """
            DELETE es
            FROM environment_servers es
            JOIN servers s ON s.id = es.server_id
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            WHERE s.id = %s
        """
        self._sql.execute(query, (group_id, server_id))

        # Delete from 'servers'
        query = """
            DELETE s
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            WHERE s.id = %s
        """
        self._sql.execute(query, (group_id, server_id))

    def remove(self, group_id):
        query = """
            DELETE s
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
        """
        self._sql.execute(query, (group_id))

    def exist(self, group_id, server):
        if 'id' in server:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id AND r.name = %s AND r.group_id = %s
                    WHERE s.name = %s AND s.id != %s
                ) AS exist
            """
            return self._sql.execute(query, (server['region'], group_id, server['name'], server['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id AND r.name = %s AND r.group_id = %s
                    WHERE s.name = %s
                ) AS exist
            """
            return self._sql.execute(query, (server['region'], group_id, server['name']))[0]['exist'] == 1

    def exist_by_region(self, group_id, region_id):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.id = %s AND r.group_id = %s
            ) AS exist
        """
        return self._sql.execute(query, (region_id, group_id))[0]['exist'] == 1

    def exist_in_environment(self, group_id, server_id):
        query = """
            SELECT DISTINCT s.name AS 'server_name', e.name AS 'environment_name'
            FROM environment_servers es
            JOIN environments e ON e.id = es.environment_id
            JOIN servers s ON s.id = es.server_id AND s.id = %s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
        """
        return self._sql.execute(query, (server_id, group_id))

    def get_by_environment(self, group_id, environment_name):
        query = """
            SELECT s.*
            FROM servers s
            JOIN environment_servers es ON es.server_id = s.id
            JOIN environments e ON e.id = es.environment_id AND e.group_id = %s AND e.name = %s
        """
        return self._sql.execute(query, (group_id, environment_name))