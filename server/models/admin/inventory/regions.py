from datetime import datetime

class Regions:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, region_id=None):
        if group_id is not None:
            query = """
                SELECT r.id, r.name, r.group_id, g.name AS 'group', r.ssh_tunnel, r.hostname, r.port, r.username, r.password, r.key, r.shared, r.owner_id, u.username AS 'owner', u2.username AS 'created_by', r.created_at, u3.username AS 'updated_by', r.updated_at
                FROM regions r
                LEFT JOIN users u ON u.id = r.owner_id
                LEFT JOIN users u2 ON u2.id = r.created_by
                LEFT JOIN users u3 ON u3.id = r.updated_by
                LEFT JOIN groups g ON g.id = r.group_id
                WHERE r.group_id = %s
                ORDER BY r.id DESC
            """
            return self._sql.execute(query, (group_id))
        elif region_id is not None:
            query = """
                SELECT *
                FROM regions
                WHERE id = %s
            """
            return self._sql.execute(query, (region_id))
        else:
            query = """
                SELECT r.id, r.name, r.group_id, g.name AS 'group', r.ssh_tunnel, r.hostname, r.port, r.username, r.password, r.key, r.shared, r.owner_id, u.username AS 'owner', u2.username AS 'created_by', r.created_at, u3.username AS 'updated_by', r.updated_at
                FROM regions r
                LEFT JOIN users u ON u.id = r.owner_id
                LEFT JOIN users u2 ON u2.id = r.created_by
                LEFT JOIN users u3 ON u3.id = r.updated_by
                LEFT JOIN groups g ON g.id = r.group_id
                ORDER BY r.id DESC
            """
            return self._sql.execute(query, (group_id))

    def post(self, user, region):
        query = """
            INSERT INTO regions (name, group_id, ssh_tunnel, hostname, port, username, password, `key`, shared, owner_id, created_by, created_at)             
            SELECT %s, %s, %s, IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), %s, IF(%s = 1, NULL, %s), %s, %s
        """
        self._sql.execute(query, (region['name'], region['group_id'], region['ssh_tunnel'], region['hostname'], region['hostname'], region['port'], region['port'], region['username'], region['username'], region['password'], region['password'], region['key'], region['key'], region['shared'], region['shared'], region['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user, region):
        query = """
            UPDATE regions
            SET name = %s,
                group_id = %s,
                ssh_tunnel = %s,
                hostname = IF(%s = '', NULL, %s),
                port = IF(%s = '', NULL, %s),
                username = IF(%s = '', NULL, %s),
                password = IF(%s = '', NULL, %s),
                `key` = IF(%s = '', NULL, %s),
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (region['name'], region['group_id'], region['ssh_tunnel'], region['hostname'], region['hostname'], region['port'], region['port'], region['username'],region['username'], region['password'], region['password'], region['key'], region['key'], region['shared'], region['shared'], region['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), region['id']))

    def delete(self, region_id):
        query = "DELETE FROM regions WHERE id = %s"
        self._sql.execute(query, (region_id))

    def remove(self, group_id):
        query = """
            DELETE FROM regions
            WHERE group_id = %s
        """
        self._sql.execute(query, (group_id))

    def exist(self, region):
        if 'id' in region:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM regions
                    WHERE group_id = %s
                    AND name = %s
                    AND owner_id = %s
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (region['group_id'], region['name'], region['owner_id'], region['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM regions
                    WHERE group_id = %s
                    AND name = %s
                    AND owner_id = %s
                ) AS exist
            """
            return self._sql.execute(query, (region['group_id'], region['name'], region['owner_id']))[0]['exist'] == 1

    def get_by_environment(self, user_id, group_id, environment_name):
        query = """
            SELECT DISTINCT r.*
            FROM regions r
            JOIN servers s ON s.region_id = r.id
            JOIN environment_servers es ON es.server_id = s.id
            JOIN environments e ON e.id = es.environment_id AND e.group_id = %s AND e.name = %s
            WHERE (r.shared = 1 OR r.owner_id = %s)
        """
        return self._sql.execute(query, (group_id, environment_name, user_id))
