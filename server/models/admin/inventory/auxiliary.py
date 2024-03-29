from datetime import datetime

class Auxiliary:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, auxiliary_id=None, user_id=None):
        if user_id is not None:
            query = """
                SELECT a.id, a.name, a.group_id, g.name AS 'group', a.engine, a.version, a.hostname, a.port, a.username, a.password, a.ssl, a.ssl_client_key, a.ssl_client_certificate, a.ssl_ca_certificate, a.shared, a.owner_id, a.secured, u.username AS 'owner', u2.username AS 'created_by', a.created_at, u3.username AS 'updated_by', a.updated_at
                FROM auxiliary a
                JOIN users u0 ON u0.id = %(user_id)s
                JOIN `groups` g ON g.id = a.group_id AND g.id = u0.group_id
                LEFT JOIN users u ON u.id = a.owner_id
                LEFT JOIN users u2 ON u2.id = a.created_by
                LEFT JOIN users u3 ON u3.id = a.updated_by
                WHERE a.group_id = u0.group_id
                AND (a.shared = 1 OR a.owner_id = %(user_id)s)
                ORDER BY a.id DESC
            """
            return self._sql.execute(query, {"user_id": user_id})
        elif group_id is not None:
            query = """
                SELECT a.id, a.name, a.group_id, g.name AS 'group', a.engine, a.version, a.hostname, a.port, a.username, a.password, a.ssl, a.ssl_client_key, a.ssl_client_certificate, a.ssl_ca_certificate, a.shared, a.owner_id, a.secured, u.username AS 'owner', u2.username AS 'created_by', a.created_at, u3.username AS 'updated_by', a.updated_at
                FROM auxiliary a
                LEFT JOIN users u ON u.id = a.owner_id
                LEFT JOIN users u2 ON u2.id = a.created_by
                LEFT JOIN users u3 ON u3.id = a.updated_by
                LEFT JOIN `groups` g ON g.id = a.group_id
                WHERE a.group_id = %s
                ORDER BY a.id DESC
            """
            return self._sql.execute(query, (group_id))
        elif auxiliary_id is not None:
            query = """
                SELECT *
                FROM auxiliary
                WHERE id = %s
            """
            return self._sql.execute(query, (auxiliary_id))
        else:
            query = """
                SELECT a.id, a.name, a.group_id, g.name AS 'group', a.engine, a.version, a.hostname, a.port, a.username, a.password, a.ssl, IF(a.ssl_client_key IS NULL, NULL, '<ssl_client_key>') AS 'ssl_client_key', IF(a.ssl_client_certificate IS NULL, NULL, '<ssl_client_certificate>') AS 'ssl_client_certificate', IF(a.ssl_ca_certificate IS NULL, NULL, '<ssl_ca_certificate>') AS 'ssl_ca_certificate', a.shared, a.owner_id, a.secured, u.username AS 'owner', u2.username AS 'created_by', a.created_at, u3.username AS 'updated_by', a.updated_at, '1' AS 'active'
                FROM auxiliary a
                LEFT JOIN users u ON u.id = a.owner_id
                LEFT JOIN users u2 ON u2.id = a.created_by
                LEFT JOIN users u3 ON u3.id = a.updated_by
                LEFT JOIN `groups` g ON g.id = a.group_id
                ORDER BY a.id DESC
            """
            return self._sql.execute(query)

    def post(self, user, auxiliary):
        query = """
            INSERT INTO auxiliary (name, group_id, engine, version, hostname, port, username, password, `ssl`, `ssl_client_key`, `ssl_client_certificate`, `ssl_ca_certificate`, shared, owner_id, secured, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s, %s)
        """
        self._sql.execute(query, (auxiliary['name'], auxiliary['group_id'], auxiliary['engine'], auxiliary['version'], auxiliary['hostname'], auxiliary['port'], auxiliary['username'], auxiliary['password'], auxiliary['ssl'], auxiliary['ssl_client_key'], auxiliary['ssl_client_certificate'], auxiliary['ssl_ca_certificate'], auxiliary['shared'], auxiliary['shared'], auxiliary['owner_id'], auxiliary['secured'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user, auxiliary):
        query = """
            UPDATE auxiliary
            SET name = %s,
                group_id = %s,
                engine = %s,
                version = %s,
                hostname = %s, 
                port = %s, 
                username = %s, 
                password = %s,
                `ssl` = %s,
                `ssl_client_key` = IF(%s = '<ssl_client_key>', `ssl_client_key`, %s),
                `ssl_client_certificate` = IF(%s = '<ssl_client_certificate>', `ssl_client_certificate`, %s),
                `ssl_ca_certificate` = IF(%s = '<ssl_ca_certificate>', `ssl_ca_certificate`, %s),
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                secured = %s,
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (auxiliary['name'], auxiliary['group_id'], auxiliary['engine'], auxiliary['version'], auxiliary['hostname'], auxiliary['port'], auxiliary['username'], auxiliary['password'], auxiliary['ssl'], auxiliary['ssl_client_key'], auxiliary['ssl_client_key'], auxiliary['ssl_client_certificate'], auxiliary['ssl_client_certificate'], auxiliary['ssl_ca_certificate'], auxiliary['ssl_ca_certificate'], auxiliary['shared'], auxiliary['shared'], auxiliary['owner_id'], auxiliary['secured'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), auxiliary['id']))

    def delete(self, auxiliary_id):
        query = "DELETE FROM auxiliary WHERE id = %s"
        self._sql.execute(query, (auxiliary_id))

    def exist(self, auxiliary):
        if 'id' in auxiliary:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM auxiliary
                    WHERE BINARY name = %(name)s
                    AND group_id = %(group_id)s
                    AND (
                        (%(shared)s = 1 AND shared = 1)
                        OR (%(shared)s = 0 AND owner_id = %(owner_id)s)
                    )
                    AND id != %(id)s
                ) AS exist
            """
            return self._sql.execute(query, {"name": auxiliary['name'], "group_id": auxiliary['group_id'], "owner_id": auxiliary['owner_id'], "shared": auxiliary['shared'], "id": auxiliary['id']})[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM auxiliary
                    WHERE BINARY name = %(name)s
                    AND group_id = %(group_id)s
                    AND (
                        (%(shared)s = 1 AND shared = 1)
                        OR (%(shared)s = 0 AND owner_id = %(owner_id)s)
                    )
                ) AS exist
            """
            return self._sql.execute(query, {"name": auxiliary['name'], "group_id": auxiliary['group_id'], "owner_id": auxiliary['owner_id'], "shared": auxiliary['shared']})[0]['exist'] == 1
