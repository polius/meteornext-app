class Client:
    def __init__(self, sql):
        self._sql = sql

    def get_servers(self, group_id):
        query = """
            SELECT s.id AS 'server_id', s.name AS 'server_name', s.engine AS 'server_engine', r.id AS 'region_id', r.name AS 'region_name'
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
    