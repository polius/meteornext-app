from datetime import datetime

class Regions:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id, region_id=None):
        if region_id is None:
            query = """
                SELECT *
                FROM regions 
                WHERE group_id = %s
            """
            return self._sql.execute(query, (group_id))
        else:
            query = """
                SELECT *
                FROM regions 
                WHERE group_id = %s
                AND r.id = %s
            """
            return self._sql.execute(query, (group_id, region_id))            

    def post(self, user_id, group_id, region):
        query = """
            INSERT INTO regions (name, group_id, ssh_tunnel, hostname, port, username, password, `key`, created_by, created_at)             
            SELECT %s, %s, %s, IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), %s, %s
        """
        self._sql.execute(query, (region['name'], group_id, region['ssh_tunnel'], region['hostname'], region['hostname'], region['port'], region['port'], region['username'], region['username'], region['password'], region['password'], region['key'], region['key'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group_id, region):
        query = """
            UPDATE regions
            SET name = %s,
                ssh_tunnel = %s,
                hostname = IF(%s = '', NULL, %s),
                port = IF(%s = '', NULL, %s),
                username = IF(%s = '', NULL, %s),
                password = IF(%s = '', NULL, %s),
                `key` = IF(%s = '', NULL, %s),
                updated_by = %s,
                updated_at = %s
            WHERE group_id = %s 
            AND id = %s
        """
        self._sql.execute(query, (region['name'], region['ssh_tunnel'], region['hostname'], region['hostname'], region['port'], region['port'], region['username'],region['username'], region['password'], region['password'], region['key'], region['key'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), group_id, region['id']))

    def delete(self, group_id, region_id):
        query = """
            DELETE FROM regions
            WHERE group_id = %s
            AND id = %s
        """
        self._sql.execute(query, (group_id, region_id))

    def remove(self, group_id):
        query = """
            DELETE FROM regions
            WHERE group_id = %s
        """
        self._sql.execute(query, (group_id))

    def exist(self, group_id, region):
        if 'id' in region:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM regions
                    WHERE group_id = %s
                    AND name = %s
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (group_id, region['name'], region['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM regions
                    WHERE group_id = %s
                    AND name = %s
                ) AS exist
            """
            return self._sql.execute(query, (group_id, region['name']))[0]['exist'] == 1

    def get_by_server(self, group_id, server_name):
        query = """
            SELECT *
            FROM regions
            WHERE group_id = %s 
            AND name = %s
        """
        return self._sql.execute(query, (group_id, server_name))

    def get_by_environment(self, group_id, environment_name):
        query = """
            SELECT DISTINCT r.*
            FROM regions r
            JOIN servers s ON s.region_id = r.id
            JOIN environment_servers es ON es.server_id = s.id
            JOIN environments e ON e.id = es.environment_id AND e.group_id = %s AND e.name = %s
        """
        return self._sql.execute(query, (group_id, environment_name))
