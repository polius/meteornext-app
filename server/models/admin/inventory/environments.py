from datetime import datetime

class Environments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None):
        if group_id is not None:
            query = """
                SELECT e.*, u.username AS 'owner' 
                FROM environments e
                LEFT JOIN users u ON u.id = e.owner_id 
                WHERE e.group_id = %s
                ORDER BY e.`name`
            """
            return self._sql.execute(query, (group_id))
        else:
            query = """
                SELECT e.*, u.username AS 'owner'  
                FROM environments e
                LEFT JOIN users u ON u.id = e.owner_id 
                ORDER BY e.`name`
            """
            return self._sql.execute(query)

    def post(self, user_id, group_id, environment):
        query = """
            INSERT INTO environments (name, group_id, shared, owner_id, created_by, created_at) 
            SELECT %s, %s, %s, IF(%s = 1, NULL, %s), %s, %s
        """
        environment_id = self._sql.execute(query, (environment['name'], group_id, environment['shared'], environment['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
        if len(environment['servers']) > 0:
            values = ''
            for server in environment['servers']:
                values += '(%s, %s),' % (environment_id, server)
            self._sql.execute("INSERT INTO environment_servers (environment_id, server_id) VALUES {}".format(values[:-1]))

    def put(self, user_id, group_id, environment):
        # Update environment
        query = """
            UPDATE environments 
            SET name = %s,
                shared = %s,
                owner_id = IF(%s = 1, NULL, %s),
                updated_by = %s, 
                updated_at = %s
            WHERE id = %s
            AND group_id = %s;
        """
        self._sql.execute(query, (environment['name'], environment['shared'], environment['shared'], user_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), environment['id'], group_id))

        # Clean environment servers
        query = """
            DELETE es
            FROM environment_servers es
            JOIN environments e ON e.id = es.environment_id AND e.group_id = %s AND e.id = %s
        """
        self._sql.execute(query, (group_id, environment['id']))

        # Fill environment servers
        if len(environment['servers']) > 0:
            values = ''
            for server in environment['servers']:
                values += '(%s, %s),' % (environment['id'], server)
            self._sql.execute("INSERT INTO environment_servers (environment_id, server_id) VALUES {}".format(values[:-1]))

    def delete(self, group_id, environment):
        self._sql.execute("DELETE es FROM environment_servers es JOIN environments e ON e.id = es.environment_id AND e.id = %s AND e.group_id = %s", (environment, group_id))
        self._sql.execute("DELETE FROM environments WHERE id = %s AND group_id = %s", (environment, group_id))

    def remove(self, group_id):
        self._sql.execute("DELETE es FROM environment_servers es JOIN environments e ON e.id = es.environment_id AND e.group_id = %s", (group_id))
        self._sql.execute("DELETE FROM environments WHERE group_id = %s", (group_id))

    def exist(self, user_id, group_id, environment):
        if 'id' in environment:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM environments 
                    WHERE name = %s 
                    AND group_id = %s
                    AND owner_id = %s
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (environment['name'], group_id, user_id, environment['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM environments 
                    WHERE name = %s
                    AND owner_id = %s
                    AND group_id = %s
                ) AS exist
            """
            return self._sql.execute(query, (environment['name'], user_id, group_id))[0]['exist'] == 1

    def get_by_name(self, user_id, group_id, environment_name):
        query = """
            SELECT *
            FROM environments
            WHERE group_id = %s
            AND name = %s
            AND (shared = 1 OR owner_id = %s)
        """
        return self._sql.execute(query, (group_id, environment_name, user_id))

    def get_servers(self, group_id=None):
        if group_id is not None:
            query = """
                SELECT s.id AS 'server_id', s.name AS 'server_name', s.shared AS 'server_shared', r.id AS 'region_id', r.name AS 'region_name'
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            """
            return self._sql.execute(query, (group_id))
        else:
            query = """
                SELECT s.id AS 'server_id', s.name AS 'server_name', s.shared AS 'server_shared', r.id AS 'region_id', r.name AS 'region_name'
                FROM servers s
                JOIN regions r ON r.id = s.region_id
            """
            return self._sql.execute(query)

    def get_environment_servers(self, group_id=None):
        if group_id is not None:
            query = """
                SELECT es.environment_id, s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name'
                FROM environment_servers es
                JOIN environments e ON e.id = es.environment_id AND e.group_id = %s
                JOIN servers s ON s.id = es.server_id
                JOIN regions r ON r.id = s.region_id
            """
            return self._sql.execute(query, (group_id))
        else:
            query = """
                SELECT es.environment_id, s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name'
                FROM environment_servers es
                JOIN environments e ON e.id = es.environment_id
                JOIN servers s ON s.id = es.server_id
                JOIN regions r ON r.id = s.region_id
            """
            return self._sql.execute(query)
