from datetime import datetime

class Auxiliary:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id, group_id, auxiliary_id=None):
        if auxiliary_id is None:
            query = """
                SELECT a.id, a.name, a.group_id, a.engine, a.version, a.hostname, a.port, a.username, a.password, a.`ssl`, a.ssl_client_key, a.ssl_client_certificate, a.ssl_ca_certificate, a.shared, a.owner_id, a.secured, a.created_by, a.created_at
                FROM auxiliary a
                WHERE a.group_id = %(group_id)s
                AND (a.shared = 1 OR a.owner_id = %(user_id)s)
                ORDER BY a.id DESC
            """
            return self._sql.execute(query, {"group_id": group_id, "user_id": user_id})
        else:
            query = """
                SELECT id, name, group_id, engine, version, hostname, port, username, password, `ssl`, ssl_client_key, ssl_client_certificate, ssl_ca_certificate, shared, owner_id, secured, created_by, created_at
                FROM auxiliary
                WHERE group_id = %s
                AND (shared = 1 OR owner_id = %s)
                AND id = %s
            """
            return self._sql.execute(query, (group_id, user_id, auxiliary_id))

    def post(self, user_id, group_id, auxiliary):
        query = """
            INSERT INTO auxiliary (name, group_id, engine, version, hostname, port, username, password, `ssl`, `ssl_client_key`, `ssl_client_certificate`, `ssl_ca_certificate`, shared, owner_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s)
        """
        self._sql.execute(query, (auxiliary['name'], group_id, auxiliary['engine'], auxiliary['version'], auxiliary['hostname'], auxiliary['port'], auxiliary['username'], auxiliary['password'], auxiliary['ssl'], auxiliary['ssl_client_key'], auxiliary['ssl_client_certificate'], auxiliary['ssl_ca_certificate'], auxiliary['shared'], auxiliary['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group_id, auxiliary):
        query = """
            UPDATE auxiliary
            SET name = %s,
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
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
            AND group_id = %s
        """
        self._sql.execute(query, (auxiliary['name'], auxiliary['engine'], auxiliary['version'], auxiliary['hostname'], auxiliary['port'], auxiliary['username'], auxiliary['password'], auxiliary['ssl'], auxiliary['ssl_client_key'], auxiliary['ssl_client_key'], auxiliary['ssl_client_certificate'], auxiliary['ssl_client_certificate'], auxiliary['ssl_ca_certificate'], auxiliary['ssl_ca_certificate'], auxiliary['shared'], auxiliary['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), auxiliary['id'], group_id))

    def delete(self, user_id, group_id, auxiliary_id):
        query = """
            DELETE FROM auxiliary
            WHERE group_id = %s
            AND (shared = 1 OR owner_id = %s)
            AND id = %s
        """
        self._sql.execute(query, (group_id, user_id, auxiliary_id))

    def exist(self, user_id, group_id, auxiliary):
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
            return self._sql.execute(query, {"name": auxiliary['name'], "group_id": group_id, "owner_id": user_id, "shared": auxiliary['shared'], "id": auxiliary['id']})[0]['exist'] == 1
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
            return self._sql.execute(query, {"name": auxiliary['name'], "group_id": group_id, "owner_id": user_id, "shared": auxiliary['shared']})[0]['exist'] == 1
