from datetime import datetime

class Cloud:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id, group_id, cloud_id=None):
        if cloud_id is None:
            query = """
                SELECT id, name, group_id, type, access_key, secret_key, shared, owner_id, created_by, created_at
                FROM cloud
                WHERE group_id = %s
                AND (shared = 1 OR owner_id = %s)
                ORDER BY `name`
            """
            return self._sql.execute(query, (group_id, user_id))
        else:
            query = """
                SELECT id, name, group_id, type, access_key, secret_key, shared, owner_id, created_by, created_at
                FROM cloud
                WHERE group_id = %s
                AND (shared = 1 OR owner_id = %s)
                AND id = %s
            """
            return self._sql.execute(query, (group_id, user_id, cloud_id))

    def post(self, user_id, group_id, cloud):
        query = """
            INSERT INTO cloud (name, group_id, type, access_key, secret_key, shared, owner_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s)
        """
        self._sql.execute(query, (cloud['name'], group_id, cloud['type'], cloud['access_key'], cloud['secret_key'], cloud['shared'], cloud['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group_id, cloud):
        query = """
            UPDATE cloud
            SET name = %s,
                type = %s,
                access_key = %s,
                secret_key = %s,
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
            AND group_id = %s
        """
        self._sql.execute(query, (cloud['name'], cloud['type'], cloud['access_key'], cloud['secret_key'], cloud['shared'], cloud['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), cloud['id'], group_id))

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
                    WHERE name = %s
                    AND group_id = %s
                    AND (
                        (shared = 1 AND shared = %s) OR (shared = 0 AND shared = %s AND owner_id = %s)
                    )
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (cloud['name'], group_id, cloud['shared'], cloud['shared'], user_id, cloud['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM cloud
                    WHERE name = %s
                    AND group_id = %s
                    AND (
                        (shared = 1 AND shared = %s) OR (shared = 0 AND shared = %s AND owner_id = %s)
                    )
                ) AS exist
            """
            return self._sql.execute(query, (cloud['name'], group_id, cloud['shared'], cloud['shared'], user_id))[0]['exist'] == 1
