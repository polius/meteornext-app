class Utils:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def get_servers(self, user):
        query = """
            SELECT s.id, s.name, s.shared, s.secured, t.id IS NOT NULL AS 'active'
            FROM servers s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = %(user_id)s)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            WHERE s.group_id = %(group_id)s
            AND (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%U%%'
            ORDER BY s.name
        """
        return self._sql.execute(query, {"user_id": user['id'], "group_id": user['group_id'], "license": self._license.get_resources()})

    def get_credentials(self, user_id, group_id, server_id):
        query = """
            SELECT 
                s.id, s.engine, s.hostname, s.port, s.username, s.password,
                s.ssl, s.ssl_client_key, s.ssl_client_certificate, s.ssl_ca_certificate,
                t.id IS NOT NULL AS 'active',
                r.ssh_tunnel AS 'rtunnel', r.hostname AS 'rhostname', r.port AS 'rport', r.username AS 'rusername', r.password AS 'rpassword', r.key AS 'rkey'
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %(group_id)s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = %(user_id)s)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            WHERE s.id = %(server_id)s
            AND (s.shared = 1 OR s.owner_id = %(user_id)s)
        """
        result = self._sql.execute(query, {"group_id": group_id, "user_id": user_id, "server_id": server_id, "license": self._license.get_resources()})
        if len(result) == 0:
            return None

        credentials = {
            'id': result[0]['id'],
            'active': result[0]['active'],
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
                'password': result[0]['password'],
                'ssl': result[0]['ssl'],
                'ssl_client_key': result[0]['ssl_client_key'],
                'ssl_client_certificate': result[0]['ssl_client_certificate'],
                'ssl_ca_certificate': result[0]['ssl_ca_certificate']
            }
        }
        return credentials
