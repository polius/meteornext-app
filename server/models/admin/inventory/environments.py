from datetime import datetime

class Environments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, user_id=None):
        if user_id is not None:
            query = """
                SELECT e.id, e.name, e.group_id, e.shared, e.owner_id, u2.username AS 'created_by', e.created_at, u3.username AS 'updated_by', e.updated_at, u.username AS 'owner', g.name AS 'group', COUNT(es.server_id) AS 'servers'
                FROM environments e
                JOIN users u0 ON u0.id = %(user_id)s
                JOIN groups g ON g.id = e.group_id AND g.id = u0.group_id
                LEFT JOIN environment_servers es ON es.environment_id = e.id
                LEFT JOIN users u ON u.id = e.owner_id
                LEFT JOIN users u2 ON u2.id = e.created_by
                LEFT JOIN users u3 ON u3.id = e.updated_by
                WHERE (e.shared = 1 OR e.owner_id = %(user_id)s)
                GROUP BY e.id
                ORDER BY e.id DESC
            """
            return self._sql.execute(query, {"user_id": user_id})
        elif group_id is not None:
            query = """
                SELECT e.id, e.name, e.group_id, e.shared, e.owner_id, u2.username AS 'created_by', e.created_at, u3.username AS 'updated_by', e.updated_at, u.username AS 'owner', g.name AS 'group', COUNT(es.server_id) AS 'servers'
                FROM environments e
                LEFT JOIN environment_servers es ON es.environment_id = e.id
                LEFT JOIN users u ON u.id = e.owner_id
                LEFT JOIN users u2 ON u2.id = e.created_by
                LEFT JOIN users u3 ON u3.id = e.updated_by
                LEFT JOIN groups g ON g.id = e.group_id
                WHERE e.group_id = %s
                GROUP BY e.id
                ORDER BY e.id DESC
            """
            return self._sql.execute(query, (group_id))
        else:
            query = """
                SELECT e.id, e.name, e.group_id, e.shared, e.owner_id, u2.username AS 'created_by', e.created_at, u3.username AS 'updated_by', e.updated_at, u.username AS 'owner', g.name AS 'group', COUNT(es.server_id) AS 'servers'
                FROM environments e
                LEFT JOIN environment_servers es ON es.environment_id = e.id
                LEFT JOIN users u ON u.id = e.owner_id
                LEFT JOIN users u2 ON u2.id = e.created_by
                LEFT JOIN users u3 ON u3.id = e.updated_by
                LEFT JOIN groups g ON g.id = e.group_id
                GROUP BY e.id
                ORDER BY e.id DESC
            """
            return self._sql.execute(query)

    def post(self, user, environment):
        query = """
            INSERT INTO environments (name, group_id, shared, owner_id, created_by, created_at) 
            SELECT %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s
        """
        environment_id = self._sql.execute(query, (environment['name'], environment['group_id'], environment['shared'], environment['shared'], environment['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
        if len(environment['servers']) > 0:
            values = ''
            for server in environment['servers']:
                values += '(%s, %s),' % (environment_id, server)
            self._sql.execute("INSERT INTO environment_servers (environment_id, server_id) VALUES {}".format(values[:-1]))

    def put(self, user, environment):
        # Clean environment servers
        query = """
            DELETE es
            FROM environment_servers es
            JOIN environments e ON e.id = es.environment_id AND e.id = %s
        """
        self._sql.execute(query, (environment['id']))

        # Update environment
        query = """
            UPDATE environments 
            SET name = %s,
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                updated_by = %s, 
                updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (environment['name'], environment['shared'], environment['shared'], environment['owner_id'], user['id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), environment['id']))

        # Fill environment servers
        if len(environment['servers']) > 0:
            values = ''
            for server in environment['servers']:
                values += '(%s, %s),' % (environment['id'], server)
            self._sql.execute("INSERT IGNORE INTO environment_servers (environment_id, server_id) VALUES {}".format(values[:-1]))

    def delete(self, environment):
        self._sql.execute("UPDATE executions SET environment_id = NULL WHERE environment_id = %s", (environment))
        self._sql.execute("DELETE es FROM environment_servers es JOIN environments e ON e.id = es.environment_id AND e.id = %s", (environment))
        self._sql.execute("DELETE FROM environments WHERE id = %s", (environment))

    def exist(self, environment):
        if 'id' in environment:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM environments
                    WHERE BINARY name = %(name)s
                    AND group_id = %(group_id)s
                    AND (
                        (%(shared)s = 1 AND shared = 1)
                        OR (%(shared)s = 0 AND owner_id = %(owner_id)s)
                    )
                    AND id != %(id)s
                ) AS exist
            """
            return self._sql.execute(query, {"name": environment['name'], "group_id": environment['group_id'], "owner_id": environment['owner_id'], "shared": environment['shared'], "id": environment['id']})[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM environments
                    WHERE BINARY name = %(name)s
                    AND group_id = %(group_id)s
                    AND (
                        (%(shared)s = 1 AND shared = 1)
                        OR (%(shared)s = 0 AND owner_id = %(owner_id)s)
                    )
                ) AS exist
            """
            return self._sql.execute(query, {"name": environment['name'], "group_id": environment['group_id'], "owner_id": environment['owner_id'], "shared": environment['shared']})[0]['exist'] == 1

    def get_servers(self, group_id, owner_id=None):
        if owner_id is not None:
            query = """
                SELECT s.id AS 'server_id', s.name AS 'server_name', s.shared AS 'server_shared', s.owner_id AS 'server_owner', r.id AS 'region_id', r.name AS 'region_name'
                FROM servers s
                LEFT JOIN regions r ON r.id = s.region_id
                WHERE r.group_id = %s
                AND (s.shared = 1 OR s.owner_id = %s)
            """
            return self._sql.execute(query, (group_id, owner_id))
        else:
            query = """
                SELECT s.id AS 'server_id', s.name AS 'server_name', s.shared AS 'server_shared', s.owner_id AS 'server_owner', r.id AS 'region_id', r.name AS 'region_name'
                FROM servers s
                LEFT JOIN regions r ON r.id = s.region_id
                WHERE r.group_id = %s
                AND s.shared = 1
            """
            return self._sql.execute(query, (group_id))

    def get_environment_servers(self, group_id, owner_id=None):
        if owner_id is not None:
            query = """
                SELECT es.environment_id, s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name'
                FROM environment_servers es
                JOIN environments e ON e.id = es.environment_id AND e.group_id = %s
                JOIN servers s ON s.id = es.server_id AND (s.shared = 1 OR s.owner_id = %s)
                LEFT JOIN regions r ON r.id = s.region_id
            """
            return self._sql.execute(query, (group_id, owner_id))
        else:
            query = """
                SELECT es.environment_id, s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name'
                FROM environment_servers es
                JOIN environments e ON e.id = es.environment_id AND e.group_id = %s
                JOIN servers s ON s.id = es.server_id AND s.shared = 1
                LEFT JOIN regions r ON r.id = s.region_id
            """
            return self._sql.execute(query, (group_id))
