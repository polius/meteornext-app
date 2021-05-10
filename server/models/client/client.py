from datetime import datetime

class Client:
    def __init__(self, sql):
        self._sql = sql

    def get_servers(self, user_id, group_id):
        query = """
            SELECT s.*, cs.folder_id, cf.name AS 'folder_name', r.name AS 'region', r.shared AS 'region_shared', r.ssh_tunnel AS 'ssh_enabled', r.hostname AS 'ssh_hostname', r.`port` AS 'ssh_port', r.username AS 'ssh_username', r.`password` AS 'ssh_password', r.`key` AS 'ssh_key'
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %(group_id)s
            JOIN client_servers cs ON cs.server_id = s.id AND cs.user_id = %(user_id)s
            LEFT JOIN client_folders cf ON cf.id = cs.folder_id
            WHERE s.group_id = %(group_id)s AND (s.shared = 1 OR s.owner_id = %(user_id)s)
            ORDER BY s.name;
        """
        return self._sql.execute(query, {"user_id": user_id, "group_id": group_id})

    def get_servers_unassigned(self, user_id, group_id):
        query = """
            SELECT s.*, cs.folder_id, r.name AS 'region', r.shared AS 'region_shared', r.ssh_tunnel AS 'ssh_enabled', r.hostname AS 'ssh_hostname', r.`port` AS 'ssh_port', r.username AS 'ssh_username', r.`password` AS 'ssh_password', r.`key` AS 'ssh_key'
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %(group_id)s
            LEFT JOIN client_servers cs ON cs.server_id = s.id AND cs.user_id = %(user_id)s
            WHERE s.group_id = %(group_id)s
            AND (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%C%%'
            AND cs.server_id IS NULL
            ORDER BY s.name;
        """
        return self._sql.execute(query, {"user_id": user_id, "group_id": group_id})

    def get_folders(self, user_id):
        query = """
            SELECT cf.id, cf.name
            FROM client_folders cf
            WHERE cf.user_id = %s
            ORDER BY cf.name
        """
        return self._sql.execute(query, (user_id))

    def get_credentials(self, user_id, group_id, server_id):
        query = """
            SELECT 
                s.id, s.engine, s.hostname, s.port, s.username, s.password,
                r.ssh_tunnel AS 'rtunnel', r.hostname AS 'rhostname', r.port AS 'rport', r.username AS 'rusername', r.password AS 'rpassword', r.key AS 'rkey'
            FROM servers s
            JOIN regions r ON r.id = s.region_id AND r.group_id = %s
            WHERE s.id = %s
            AND (s.shared = 1 OR s.owner_id = %s)
        """
        result = self._sql.execute(query, (group_id, server_id, user_id))
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

    def get_settings(self, user_id):
        query = """
            SELECT setting, value
            FROM client_settings
            WHERE user_id = %s
        """
        return self._sql.execute(query, (user_id))

    def save_settings(self, user_id, data):
        for k, v in data.items():
            query = """
                INSERT INTO client_settings (user_id, setting, value)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE value = VALUES(value)
            """
            self._sql.execute(query, (user_id, k, v))

    def add_servers(self, data, user):
        for server in data:
            query = """
                INSERT INTO client_servers (user_id, server_id) 
                SELECT %s, id
                FROM servers
                WHERE group_id = %s
                AND (shared = 1 OR owner_id = %s)
                AND id = %s
            """
            self._sql.execute(query, (user['id'], user['group_id'], user['id'], server))
    
    def remove_servers(self, data, user_id):
        for server in data:
            query = "DELETE FROM client_servers WHERE user_id = %s AND server_id = %s"
            self._sql.execute(query, (user_id, server))

    def move_servers(self, data, user):
        for server in data['servers']:
            query = """
                UPDATE client_servers
                JOIN servers s ON s.id = client_servers.server_id
                SET client_servers.folder_id = %s
                WHERE client_servers.user_id = %s
                AND client_servers.server_id = %s
                AND s.group_id = %s
                AND (s.shared = 1 OR s.owner_id = %s)
            """
            self._sql.execute(query, (data['folder'], user['id'], server, user['group_id'], user['id']))

    def add_folder(self, folder_name, user_id):
        query = "INSERT INTO client_folders (name, user_id) VALUES (%s, %s)"
        self._sql.execute(query, (folder_name, user_id))

    def remove_folders(self, data, user_id):
        for folder in data:
            query = """
                UPDATE client_servers
                JOIN client_folders cf ON cf.id = client_servers.folder_id AND cf.user_id = %s
                SET client_servers.folder_id = NULL
                WHERE client_servers.folder_id = %s
            """
            self._sql.execute(query, (user_id, folder))
            query = "DELETE FROM client_folders WHERE id = %s AND user_id = %s"
            self._sql.execute(query, (folder, user_id))

    def rename_folder(self, folder, user_id):
        query = "UPDATE client_folders SET name = %s WHERE id = %s AND user_id = %s"
        self._sql.execute(query, (folder['name'], folder['id'], user_id))

    def exists_folder(self, folder, user_id):
        if 'id' in folder:
            query = """
                SELECT EXISTS(
                    SELECT *
                    FROM client_folders
                    WHERE name = %s
                    AND id != %s
                    AND user_id = %s
                ) AS exist
            """
            return self._sql.execute(query, (folder['name'], folder['id'], user_id))[0]['exist']
        else:
            query = """
                SELECT EXISTS(
                    SELECT *
                    FROM client_folders
                    WHERE name = %s
                    AND user_id = %s
                ) AS exist
            """
            return self._sql.execute(query, (folder['name'], user_id))[0]['exist']

    def track_query(self, user_id, server_id, database, query, status, records=None, elapsed=None, error=None):
        query2 = """
            INSERT INTO client_queries (`date`, `user_id`, `server_id`, `database`, `query`, `status`, `records`, `elapsed`, `error`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query2, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user_id, server_id, database, query, status, records, elapsed, error))
