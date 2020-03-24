from datetime import datetime

class Environments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id, environment=None):
        if environment:
            query = """
                SELECT * 
                FROM environments
                WHERE group_id = %s
                AND id = %s
            """
            return self._sql.execute(query, (group_id, environment))
        else:
            query = """
                SELECT * 
                FROM environments
                WHERE group_id = %s
            """
            return self._sql.execute(query, (group_id))

    def post(self, user_id, group_id, environment):
        environment_id = self._sql.execute("INSERT INTO environments (name, group_id, created_by, created_at) VALUES (%s, %s, %s, %s)", (environment['name'], group_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
        values = ''
        for region in environment['servers']:
            for server in region['children']:
                values += '(%s, %s),' % (environment_id, server['id'])        
        self._sql.execute("INSERT INTO environment_servers (environment_id, server_id) VALUES {}".format(values[:-1]))

    def put(self, user_id, group_id, environment):
        # Update environment
        self._sql.execute("UPDATE environments SET name = %s, updated_by = %s, updated_at = %s WHERE id = %s AND group_id = %s", (environment['name'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), environment['id'], group_id))

        # Clean environment servers
        query = """
            DELETE es
            FROM environment_servers es
            JOIN environments e ON e.id = es.environment_id AND e.group_id = %s AND e.id = %s
        """
        self._sql.execute(query, (group_id, environment['id']))

        # Fill environment servers
        values = ''
        for region in environment['servers']:
            for server in region['children']:
                values += '(%s, %s),' % (environment['id'], server['id'])
        self._sql.execute("INSERT INTO environment_servers (environment_id, server_id) VALUES {}".format(values[:-1]))

    def delete(self, group_id, environment):
        self._sql.execute("DELETE es FROM environment_servers es JOIN environments e ON e.id = es.environment_id AND e.id = %s AND e.group_id = %s", (environment, group_id))
        self._sql.execute("DELETE FROM environments WHERE id = %s AND group_id = %s", (environment, group_id))

    def remove(self, group_id):
        self._sql.execute("DELETE es FROM environment_servers es JOIN environments e ON e.id = es.environment_id AND e.group_id = %s", (group_id))
        self._sql.execute("DELETE FROM environments WHERE group_id = %s", (group_id))

    def exist(self, group_id, environment):
        if 'id' in environment:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM environments 
                    WHERE name = %s 
                    AND group_id = %s
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (environment['name'], group_id, environment['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM environments 
                    WHERE name = %s 
                    AND group_id = %s
                ) AS exist
            """
            return self._sql.execute(query, (environment['name'], group_id))[0]['exist'] == 1

    def get_servers(self, group_id, environment=None):
        if environment:
            query = """
                SELECT s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name'
                FROM environments e
                JOIN environment_servers es ON e.id = es.environment_id
                JOIN servers s ON s.id = es.server_id
                JOIN regions r ON r.id = s.region_id
                WHERE e.id = %s
                AND e.group_id = %s
            """
            return self._sql.execute(query, (environment, group_id))
        else:
            query = """
                SELECT s.id AS 'server_id', s.name AS 'server_name', r.id AS 'region_id', r.name AS 'region_name'
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            """
            return self._sql.execute(query, (group_id))