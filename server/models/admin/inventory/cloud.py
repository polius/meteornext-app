from datetime import datetime

class Cloud:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, cloud_id=None, user_id=None):
        if user_id is not None:
            query = """
                SELECT c.id, c.name, c.group_id, g.name AS 'group', c.type, c.access_key, c.secret_key, c.buckets, c.shared, c.owner_id, c.secured, u.username AS 'owner', u2.username AS 'created_by', c.created_at, u3.username AS 'updated_by', c.updated_at
                FROM cloud c
                JOIN users u0 ON u0.id = %(user_id)s
                JOIN groups g ON g.id = c.group_id AND g.id = u0.group_id
                LEFT JOIN users u ON u.id = c.owner_id
                LEFT JOIN users u2 ON u2.id = c.created_by
                LEFT JOIN users u3 ON u3.id = c.updated_by
                WHERE (c.shared = 1 OR c.owner_id = %(user_id)s)
                ORDER BY c.id DESC
            """
            return self._sql.execute(query, {"user_id": user_id})
        elif group_id is not None:
            query = """
                SELECT c.id, c.name, c.group_id, g.name AS 'group', c.type, c.access_key, c.secret_key, c.buckets, c.shared, c.owner_id, c.secured, u.username AS 'owner', u2.username AS 'created_by', c.created_at, u3.username AS 'updated_by', c.updated_at
                FROM cloud c
                LEFT JOIN users u ON u.id = c.owner_id
                LEFT JOIN users u2 ON u2.id = c.created_by
                LEFT JOIN users u3 ON u3.id = c.updated_by
                LEFT JOIN groups g ON g.id = c.group_id
                WHERE c.group_id = %s
                ORDER BY c.id DESC
            """
            return self._sql.execute(query, (group_id))
        elif cloud_id is not None:
            query = """
                SELECT *
                FROM cloud
                WHERE id = %s
            """
            return self._sql.execute(query, (cloud_id))
        else:
            query = """
                SELECT c.id, c.name, c.group_id, g.name AS 'group', c.type, c.access_key, c.secret_key, c.buckets, c.shared, c.owner_id, c.secured, u.username AS 'owner', u2.username AS 'created_by', c.created_at, u3.username AS 'updated_by', c.updated_at
                FROM cloud c
                LEFT JOIN users u ON u.id = c.owner_id
                LEFT JOIN users u2 ON u2.id = c.created_by
                LEFT JOIN users u3 ON u3.id = c.updated_by
                LEFT JOIN groups g ON g.id = c.group_id
                ORDER BY c.id DESC
            """
            return self._sql.execute(query)

    def post(self, user, cloud):
        query = """
            INSERT INTO cloud (name, group_id, type, access_key, secret_key, buckets, shared, owner_id, secured, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s, %s)
        """
        self._sql.execute(query, (cloud['name'], cloud['group_id'], cloud['type'], cloud['access_key'], cloud['secret_key'], cloud['buckets'], cloud['shared'], cloud['shared'], cloud['owner_id'], cloud['secured'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user, cloud):
        query = """
            UPDATE cloud
            SET name = %s,
                group_id = %s,
                type = %s,
                access_key = %s,
                secret_key = IF(%s = '<secret_key>', `secret_key`, %s),
                buckets = %s,
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                secured = %s,
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (cloud['name'], cloud['group_id'], cloud['type'], cloud['access_key'], cloud['secret_key'], cloud['secret_key'], cloud['buckets'], cloud['shared'], cloud['shared'], cloud['owner_id'], cloud['secured'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), cloud['id']))

    def delete(self, cloud_id):
        query = "DELETE FROM cloud WHERE id = %s"
        self._sql.execute(query, (cloud_id))

    def exist(self, cloud):
        if 'id' in cloud:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM cloud
                    WHERE BINARY name = %(name)s
                    AND group_id = %(group_id)s
                    AND (
                        (%(shared)s = 1 AND shared = 1)
                        OR (%(shared)s = 0 AND owner_id = %(owner_id)s)
                    )
                    AND id != %(id)s
                ) AS exist
            """
            return self._sql.execute(query, {"name": cloud['name'], "group_id": cloud['group_id'], "owner_id": cloud['owner_id'], "shared": cloud['shared'], "id": cloud['id']})[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM cloud
                    WHERE BINARY name = %(name)s
                    AND group_id = %(group_id)s
                    AND (
                        (%(shared)s = 1 AND shared = 1)
                        OR (%(shared)s = 0 AND owner_id = %(owner_id)s)
                    )
                ) AS exist
            """
            return self._sql.execute(query, {"name": cloud['name'], "group_id": cloud['group_id'], "owner_id": cloud['owner_id'], "shared": cloud['shared']})[0]['exist'] == 1
