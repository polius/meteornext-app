class Client:
    def __init__(self, sql):
        self._sql = sql

    def get_servers(self, group_id):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', s.engine AS 'server_engine', s.hostname AS 'server_hostname', r.id AS 'region_id', r.name AS 'region_name'
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
        """
        return self._sql.execute(query, (group_id))

    def get_credentials(self, group_id, server_id):
        query = """
            SELECT 
                s.engine, s.hostname, s.port, s.username, s.password,
                r.ssh_tunnel AS 'rtunnel', r.hostname AS 'rhostname', r.port AS 'rport', r.username AS 'rusername', r.password AS 'rpassword', r.key AS 'rkey'
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            WHERE s.id = %s
        """
        result = self._sql.execute(query, (group_id, server_id))
        if len(result) == 0:
            return None

        credentials = {
            'ssh': {
                'enabled': result[0]['rtunnel'],
                'hostname': result[0]['rhostname'],
                'port': result[0]['rport'],
                'username': result[0]['rusername'],
                'password': result[0]['rpassword'],
                'key': result[0]['rkey']
            },
            'sql': {
                'engine': result[0]['engine'],
                'hostname': result[0]['hostname'],
                'port': result[0]['port'],
                'username': result[0]['username'],
                'password': result[0]['password']
            }
        }
        return credentials

    def get_saved_queries(self, user_id):
        query = """
            SELECT *
            FROM client_saved_queries
            WHERE user_id = %s
        """
        return self._sql.execute(query, (user_id))

    def add_saved_query(self, data, user_id):
        query = """
            INSERT INTO client_saved_queries (`name`, `query`, `user_id`)
            VALUES (%s, %s, %s)
        """
        return self._sql.execute(query, (data['name'], data['query'], user_id))

    def edit_saved_query(self, data, user_id):
        query = """
            UPDATE client_saved_queries
            SET name = %s,
            query = %s
            WHERE id = %s
            AND user_id = %s
        """
        return self._sql.execute(query, (data['name'], data['query'], data['id'], user_id))

    def delete_saved_queries(self, data, user_id):
        for s in data:
            query = "DELETE FROM client_saved_queries WHERE id = %s AND user_id = %s"
            self._sql.execute(query, (s, user_id))
