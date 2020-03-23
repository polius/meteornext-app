from datetime import datetime

class Servers:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id, server_id=None):
        if server_id is None:
            query = """
                SELECT s.*, r.name AS 'region' 
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            """
            return self._sql.execute(query, (group_id))
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
            INSERT INTO servers (name, region_id, hostname, port, username, password, created_by, created_at)             
            SELECT %s, id, %s, %s, %s, %s, %s, %s
            FROM regions
            WHERE group_id = %s
            AND name = %s
        """
        self._sql.execute(query, (server['name'], server['hostname'], server['port'], server['username'], server['password'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), group_id, server['region']))

    def put(self, user_id, group_id, server):
        query = """
            UPDATE servers
            JOIN regions r ON r.id = servers.region_id AND r.id = %s
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.id = %s
            SET servers.name = %s,
                servers.region_id = (SELECT r.id FROM regions r JOIN environments e ON e.id = r.environment_id AND e.name = %s AND e.group_id = %s WHERE r.name = %s),
                servers.hostname = %s,
                servers.port = %s,
                servers.username = %s,
                servers.password = %s,
                servers.updated_by = %s,
                servers.updated_at = %s
            WHERE servers.id = %s
        """
        self._sql.execute(query, (server['region_id'], group_id, server['environment_id'], server['name'], server['environment'], group_id, server['region'], server['hostname'], server['port'], server['username'], server['password'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), server['id']))

    def delete(self, group_id, server_id):
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