from datetime import datetime

class Cloud:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id, group_id, cloud_id=None):
        if cloud_id is None:
            query = """
                SELECT id, name, group_id, type, access_key, secret_key, buckets, shared, owner_id, created_by, created_at
                FROM cloud
                WHERE group_id = %s
                AND (shared = 1 OR owner_id = %s)
                ORDER BY `id` DESC
            """
            return self._sql.execute(query, (group_id, user_id))
        else:
            query = """
                SELECT id, name, group_id, type, access_key, secret_key, buckets, shared, owner_id, created_by, created_at
                FROM cloud
                WHERE group_id = %s
                AND (shared = 1 OR owner_id = %s)
                AND id = %s
            """
            return self._sql.execute(query, (group_id, user_id, cloud_id))

    def post(self, user_id, group_id, cloud):
        query = """
            INSERT INTO cloud (name, group_id, type, access_key, secret_key, buckets, shared, owner_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s)
        """
        self._sql.execute(query, (cloud['name'], group_id, cloud['type'], cloud['access_key'], cloud['secret_key'], cloud['buckets'], cloud['shared'], cloud['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group_id, cloud):
        query = """
            UPDATE cloud
            SET name = %s,
                type = %s,
                access_key = %s,
                secret_key = IF(%s = '<secret_key>', `secret_key`, %s),
                buckets = %s,
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
            AND group_id = %s
        """
        self._sql.execute(query, (cloud['name'], cloud['type'], cloud['access_key'], cloud['secret_key'], cloud['secret_key'], cloud['buckets'], cloud['shared'], cloud['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), cloud['id'], group_id))

    def delete(self, user_id, group_id, cloud_id):
        query = """
            DELETE FROM cloud
            WHERE group_id = %s
            AND (shared = 1 OR owner_id = %s)
            AND id = %s
        """
        self._sql.execute(query, (group_id, user_id, cloud_id))

    def exist(self, user_id, group_id, cloud):
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
            return self._sql.execute(query, {"name": cloud['name'], "group_id": group_id, "owner_id": user_id, "shared": cloud['shared'], "id": cloud['id']})[0]['exist'] == 1
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
            return self._sql.execute(query, {"name": cloud['name'], "group_id": group_id, "owner_id": user_id, "shared": cloud['shared']})[0]['exist'] == 1
