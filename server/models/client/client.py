class Client:
    def __init__(self, sql):
        self._sql = sql

    def get_servers(self, user_id):
        query = """
            SELECT s.id, s.name, s.engine, s.version, s.shared, cs.folder_id
            FROM servers s
            JOIN client_servers cs ON cs.server_id = s.id AND cs.user_id = %s
            ORDER BY s.name
        """
        return self._sql.execute(query, (user_id))

    def get_folders(self, user_id):
        query = """
            SELECT cf.id, cf.name
            FROM client_folders cf
            WHERE cf.user_id = %s
            ORDER BY cf.name
        """
        return self._sql.execute(query, (user_id))

    def get_credentials(self, group_id, server_id):
        query = """
            SELECT 
                s.id, s.engine, s.hostname, s.port, s.username, s.password,
                r.ssh_tunnel AS 'rtunnel', r.hostname AS 'rhostname', r.port AS 'rport', r.username AS 'rusername', r.password AS 'rpassword', r.key AS 'rkey'
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            WHERE s.id = %s
        """
        result = self._sql.execute(query, (group_id, server_id))
        if len(result) == 0:
            return None

        credentials = {
            'id': result[0]['id'],
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

    def get_processlist_settings(self, user_id):
        query = """
            SELECT refresh_rate, analyze_queries
            FROM client_processlist
            WHERE user_id = %s
        """
        return self._sql.execute(query, (user_id))
    
    def save_processlist_settings(self, data, user_id):
        query = """
            INSERT INTO client_processlist (user_id, refresh_rate, analyze_queries)
            VALUES (%(user_id)s, %(refresh_rate)s, %(analyze_queries)s)
            ON DUPLICATE KEY UPDATE
                refresh_rate = %(refresh_rate)s,
                analyze_queries = %(analyze_queries)s 
        """
        self._sql.execute(query, { "user_id": user_id, "refresh_rate": data['refresh_rate'], "analyze_queries": data['analyze_queries'] })

    def add_servers(self, data, user_id):
        for server in data:
            query = "INSERT INTO client_servers (user_id, server_id) VALUES (%s, %s)"
            self._sql.execute(query, (user_id, server))
    
    def remove_servers(self, data, user_id):
        for server in data:
            query = "DELETE FROM client_servers WHERE user_id = %s AND server_id = %s"
            self._sql.execute(query, (user_id, server))

    def move_servers(self, data, user_id):
        for server in data:
            query = "UPDATE client_servers SET folder_id = %s WHERE user_id = %s AND server_id = %s"
            self._sql.execute(query, (data['folder_id'], user_id, data['server_id']))
