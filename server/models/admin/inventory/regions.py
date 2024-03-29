from datetime import datetime

class Regions:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, owner_id=None, region_id=None, user_id=None):
        if region_id is not None:
            query = """
                SELECT *
                FROM regions
                WHERE id = %s
            """
            return self._sql.execute(query, (region_id))
        elif user_id is not None:
            query = """
                SELECT r.id, r.name, r.group_id, g.name AS 'group', r.ssh_tunnel, r.hostname, r.port, r.username, r.password, `key`, r.shared, r.owner_id, r.secured, u.username AS 'owner', u2.username AS 'created_by', r.created_at, u3.username AS 'updated_by', r.updated_at
                FROM regions r
                JOIN users u0 ON u0.id = %(user_id)s
                JOIN `groups` g ON g.id = r.group_id AND g.id = u0.group_id
                LEFT JOIN users u ON u.id = r.owner_id
                LEFT JOIN users u2 ON u2.id = r.created_by
                LEFT JOIN users u3 ON u3.id = r.updated_by
                WHERE (r.shared = 1 OR r.owner_id = %(user_id)s)
                ORDER BY r.id DESC
            """
            return self._sql.execute(query, {"user_id": user_id})
        elif group_id is not None:
            query = """
                SELECT r.id, r.name, r.group_id, g.name AS 'group', r.ssh_tunnel, r.hostname, r.port, r.username, r.password, `key`, r.shared, r.owner_id, r.secured, u.username AS 'owner', u2.username AS 'created_by', r.created_at, u3.username AS 'updated_by', r.updated_at
                FROM regions r
                LEFT JOIN users u ON u.id = r.owner_id
                LEFT JOIN users u2 ON u2.id = r.created_by
                LEFT JOIN users u3 ON u3.id = r.updated_by
                LEFT JOIN `groups` g ON g.id = r.group_id
                WHERE r.group_id = %s{}
                ORDER BY r.id DESC
            """
            owner_sql = '%s' if owner_id is None else ' AND (r.shared = 1 OR r.owner_id = %s)'
            owner_id = '' if owner_id is None else owner_id
            return self._sql.execute(query.format(owner_sql), (group_id, owner_id))
        else:
            query = """
                SELECT r.id, r.name, r.group_id, g.name AS 'group', r.ssh_tunnel, r.hostname, r.port, r.username, r.password, r.key, r.shared, r.owner_id, r.secured, u.username AS 'owner', u2.username AS 'created_by', r.created_at, u3.username AS 'updated_by', r.updated_at, COUNT(s.id) AS 'servers'
                FROM regions r
                LEFT JOIN servers s ON s.region_id = r.id
                LEFT JOIN users u ON u.id = r.owner_id
                LEFT JOIN users u2 ON u2.id = r.created_by
                LEFT JOIN users u3 ON u3.id = r.updated_by
                LEFT JOIN `groups` g ON g.id = r.group_id
                GROUP BY r.id
                ORDER BY r.id DESC
            """
            return self._sql.execute(query, (group_id))

    def post(self, user, region):
        query = """
            INSERT INTO regions (name, group_id, ssh_tunnel, hostname, port, username, password, `key`, shared, owner_id, secured, created_by, created_at)
            SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s, %s
        """
        self._sql.execute(query, (region['name'], region['group_id'], region['ssh_tunnel'], region['hostname'], region['port'], region['username'], region['password'], region['key'], region['shared'], region['shared'], region['owner_id'], region['secured'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user, region):
        query = """
            UPDATE regions
            SET name = %s,
                group_id = %s,
                ssh_tunnel = %s,
                hostname = %s,
                port = %s,
                username = %s,
                password = %s,
                `key` = IF(%s = '<ssh_key>', `key`, %s),
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                secured = %s,
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (region['name'], region['group_id'], region['ssh_tunnel'], region['hostname'], region['port'], region['username'], region['password'], region['key'], region['key'], region['shared'], region['shared'], region['owner_id'], region['secured'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), region['id']))

    def delete(self, region_id):
        query = "DELETE FROM regions WHERE id = %s"
        self._sql.execute(query, (region_id))

    def exist(self, region):
        if 'id' in region:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM regions
                    WHERE BINARY name = %(name)s
                    AND group_id = %(group_id)s
                    AND (
                        (%(shared)s = 1 AND shared = 1)
                        OR (%(shared)s = 0 AND owner_id = %(owner_id)s)
                    )
                    AND id != %(id)s
                ) AS exist
            """
            return self._sql.execute(query, {"name": region['name'], "group_id": region['group_id'], "owner_id": region['owner_id'], "shared": region['shared'], "id": region['id']})[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM regions
                    WHERE BINARY name = %(name)s
                    AND group_id = %(group_id)s
                    AND (
                        (%(shared)s = 1 AND shared = 1)
                        OR (%(shared)s = 0 AND owner_id = %(owner_id)s)
                    )
                ) AS exist
            """
            return self._sql.execute(query, {"name": region['name'], "group_id": region['group_id'], "owner_id": region['owner_id'], "shared": region['shared']})[0]['exist'] == 1

    def exist_in_server(self, region_id):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.id = %s
            ) AS exist
        """
        return self._sql.execute(query, (region_id))[0]['exist'] == 1