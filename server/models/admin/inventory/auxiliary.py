from datetime import datetime

class Auxiliary:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, auxiliary_id=None):
        if group_id is not None:
            query = """
                SELECT a.id, a.name, a.group_id, g.name AS 'group', a.ssh_tunnel, a.ssh_hostname, a.ssh_port, a.ssh_username, a.ssh_password, a.ssh_key, a.sql_engine, a.sql_version, a.sql_hostname, a.sql_port, a.sql_username, a.sql_password, a.sql_ssl, a.shared, a.owner_id, u.username AS 'owner', u2.username AS 'created_by', a.created_at, u3.username AS 'updated_by', a.updated_at
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
                SELECT a.id, a.name, a.group_id, g.name AS 'group', a.ssh_tunnel, a.ssh_hostname, a.ssh_port, a.ssh_username, a.ssh_password, a.ssh_key, a.sql_engine, a.sql_version, a.sql_hostname, a.sql_port, a.sql_username, a.sql_password, a.sql_ssl, a.shared, a.owner_id, u.username AS 'owner', u2.username AS 'created_by', a.created_at, u3.username AS 'updated_by', a.updated_at
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
            INSERT INTO auxiliary (name, group_id, ssh_tunnel, ssh_hostname, ssh_port, ssh_username, ssh_password, ssh_key, sql_engine, sql_version, sql_hostname, sql_port, sql_username, sql_password, sql_ssl, shared, owner_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s)
        """
        self._sql.execute(query, (auxiliary['name'], auxiliary['group_id'], auxiliary['ssh_tunnel'], auxiliary['ssh_hostname'], auxiliary['ssh_port'], auxiliary['ssh_username'], auxiliary['ssh_password'], auxiliary['ssh_key'], auxiliary['sql_engine'], auxiliary['sql_version'], auxiliary['sql_hostname'], auxiliary['sql_port'], auxiliary['sql_username'], auxiliary['sql_password'], auxiliary['sql_ssl'], auxiliary['shared'], auxiliary['shared'], auxiliary['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user, auxiliary):
        query = """
            UPDATE auxiliary
            SET name = %s,
                ssh_tunnel = %s, 
                ssh_hostname = %s,
                ssh_port = %s, 
                ssh_username = %s, 
                ssh_password = %s, 
                ssh_key = %s, 
                sql_engine = %s,
                sql_version = %s,
                sql_hostname = %s, 
                sql_port = %s, 
                sql_username = %s, 
                sql_password = %s,
                sql_ssl = %s,
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (auxiliary['name'], auxiliary['ssh_tunnel'], auxiliary['ssh_hostname'], auxiliary['ssh_port'], auxiliary['ssh_username'], auxiliary['ssh_password'], auxiliary['ssh_key'], auxiliary['sql_engine'], auxiliary['sql_version'], auxiliary['sql_hostname'], auxiliary['sql_port'], auxiliary['sql_username'], auxiliary['sql_password'], auxiliary['sql_ssl'], auxiliary['shared'], auxiliary['shared'], auxiliary['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), auxiliary['id']))

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
                    AND (shared = 1 OR owner_id = %s)
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (auxiliary['name'], auxiliary['group_id'], auxiliary['owner_id'], auxiliary['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM auxiliary
                    WHERE name = %s
                    AND group_id = %s
                    AND (shared = 1 OR owner_id = %s)
                ) AS exist
            """
            return self._sql.execute(query, (auxiliary['name'], auxiliary['group_id'], auxiliary['owner_id']))[0]['exist'] == 1
