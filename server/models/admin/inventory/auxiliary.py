from datetime import datetime

class Auxiliary:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, auxiliary_id=None):
        if group_id is not None:
            query = """
                SELECT a.id, a.name, a.group_id, g.name AS 'group', a.engine, a.version, a.hostname, a.port, a.username, a.password, a.ssl, a.shared, a.owner_id, u.username AS 'owner', u2.username AS 'created_by', a.created_at, u3.username AS 'updated_by', a.updated_at
                FROM auxiliary a
                LEFT JOIN users u ON u.id = a.owner_id
                LEFT JOIN users u2 ON u2.id = a.created_by
                LEFT JOIN users u3 ON u3.id = a.updated_by
                LEFT JOIN groups g ON g.id = a.group_id
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
                SELECT a.id, a.name, a.group_id, g.name AS 'group', a.engine, a.version, a.hostname, a.port, a.username, a.password, a.ssl, a.shared, a.owner_id, u.username AS 'owner', u2.username AS 'created_by', a.created_at, u3.username AS 'updated_by', a.updated_at
                FROM auxiliary a
                LEFT JOIN users u ON u.id = a.owner_id
                LEFT JOIN users u2 ON u2.id = a.created_by
                LEFT JOIN users u3 ON u3.id = a.updated_by
                LEFT JOIN groups g ON g.id = a.group_id
                ORDER BY a.id DESC
            """
            return self._sql.execute(query)

    def post(self, user, auxiliary):
        query = """
            INSERT INTO auxiliary (name, group_id, engine, version, hostname, port, username, password, ssl, shared, owner_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s)
        """
        self._sql.execute(query, (auxiliary['name'], auxiliary['group_id'], auxiliary['engine'], auxiliary['version'], auxiliary['hostname'], auxiliary['port'], auxiliary['username'], auxiliary['password'], auxiliary['ssl'], auxiliary['shared'], auxiliary['shared'], auxiliary['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user, auxiliary):
        query = """
            UPDATE auxiliary
            SET name = %s,
                engine = %s,
                version = %s,
                hostname = %s, 
                port = %s, 
                username = %s, 
                password = %s,
                ssl = %s,
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (auxiliary['name'], auxiliary['engine'], auxiliary['version'], auxiliary['hostname'], auxiliary['port'], auxiliary['username'], auxiliary['password'], auxiliary['ssl'], auxiliary['shared'], auxiliary['shared'], auxiliary['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), auxiliary['id']))

    def delete(self, auxiliary_id):
        query = "DELETE FROM auxiliary WHERE id = %s"
        self._sql.execute(query, (auxiliary_id))

    def exist(self, auxiliary):
        if 'id' in auxiliary:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM auxiliary
                    WHERE name = %s
                    AND group_id = %s
                    AND (
                        (shared = 1 AND shared = %s) OR (shared = 0 AND shared = %s AND owner_id = %s)
                    )
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (auxiliary['name'], auxiliary['group_id'], auxiliary['shared'], auxiliary['shared'], auxiliary['owner_id'], auxiliary['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM auxiliary
                    WHERE name = %s
                    AND group_id = %s
                    AND (
                        (shared = 1 AND shared = %s) OR (shared = 0 AND shared = %s AND owner_id = %s)
                    )
                ) AS exist
            """
            return self._sql.execute(query, (auxiliary['name'], auxiliary['group_id'], auxiliary['shared'], auxiliary['shared'], auxiliary['owner_id']))[0]['exist'] == 1
