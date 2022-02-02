import json

class Exports:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def get(self, user_id=None, export_uri=None):
        if export_uri:
            query = """
                SELECT e.*, s.name AS 'server_name', s.shared AS 'server_shared', q.queue
                FROM exports e
                JOIN servers s ON s.id = e.server_id
                LEFT JOIN
                (
                    SELECT (@cnt := @cnt + 1) AS queue, source_id, source_type
                    FROM (
                        SELECT i.id AS 'source_id', 'import' AS 'source_type', i.created
                        FROM imports i
                        WHERE i.status = 'QUEUED'
                        UNION ALL
                        SELECT e.id AS 'source_id', 'export' AS 'source_type', e.created
                        FROM exports e
                        WHERE e.status = 'QUEUED'
                        UNION ALL
                        SELECT c.id AS 'source_id', 'clone' AS 'source_type', c.created
                        FROM clones c
                        WHERE c.status = 'QUEUED'
                        ORDER BY created
                    ) t
                    JOIN (SELECT @cnt := 0) cnt
                ) q ON q.source_id = e.id AND q.source_type = 'export'
                WHERE e.uri = %s
            """
            return self._sql.execute(query, (export_uri))
        else:
            query = """
                SELECT e.*, s.name AS 'server_name', s.shared AS 'server_shared', q.queue
                FROM exports e
                JOIN servers s ON s.id = e.server_id
                LEFT JOIN
                (
                    SELECT (@cnt := @cnt + 1) AS queue, source_id, source_type
                    FROM (
                        SELECT i.id AS 'source_id', 'import' AS 'source_type', i.created
                        FROM imports i
                        WHERE i.status = 'QUEUED'
                        UNION ALL
                        SELECT e.id AS 'source_id', 'export' AS 'source_type', e.created
                        FROM exports e
                        WHERE e.status = 'QUEUED'
                        UNION ALL
                        SELECT c.id AS 'source_id', 'clone' AS 'source_type', c.created
                        FROM clones c
                        WHERE c.status = 'QUEUED'
                        ORDER BY created
                    ) t
                    JOIN (SELECT @cnt := 0) cnt
                ) q ON q.source_id = e.id AND q.source_type = 'export'
                WHERE e.user_id = %s
                AND e.deleted = 0
                ORDER BY e.id DESC
            """
            return self._sql.execute(query, (user_id))

    def post(self, user, data):
        query = """
            INSERT INTO exports (`server_id`, `database`, `mode`, `format`, `tables`, `export_schema`, `export_data`, `add_drop_table`, `export_triggers`, `export_routines`, `export_events`, `size`, `status`, `created`, `url`, `uri`, `user_id`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (data['server_id'], data['database'], data['mode'], data['format'], data['tables'], data['export_schema'], data['export_data'], data['add_drop_table'], data['export_triggers'], data['export_routines'], data['export_events'], data['size'], data['status'], data['created'], data['url'], data['uri'], user['id']))

    def delete(self, user, item):
        query = """
            UPDATE exports
            SET deleted = 1
            WHERE uri = %s
            AND user_id = %s
        """
        self._sql.execute(query, (item, user['id']))

    def get_servers(self, user):
        query = """
            SELECT s.id, s.name, s.shared, t.id IS NOT NULL AS 'active'
            FROM servers s
            LEFT JOIN (
                SELECT s.id
                FROM servers s
                JOIN (SELECT @cnt := 0) t
                WHERE s.group_id = %(group_id)s
                AND (s.shared = 1 OR s.owner_id = 1)
                AND (%(license)s = -1 OR (@cnt := @cnt + 1) <= %(license)s)
                ORDER BY s.id
            ) t ON t.id = s.id
            WHERE s.group_id = %(group_id)s
            AND (s.shared = 1 OR s.owner_id = %(user_id)s)
            AND s.usage LIKE '%%U%%'
            ORDER BY s.name
        """
        return self._sql.execute(query, {"user_id": user['id'], "group_id": user['group_id'], "license": self._license.resources})

    def get_credentials(self, user_id, group_id, server_id):
        query = """
            SELECT 
                s.id, s.engine, s.hostname, s.port, s.username, s.password,
                s.ssl, s.ssl_client_key, s.ssl_client_certificate, s.ssl_ca_certificate, s.ssl_verify_ca,
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
        result = self._sql.execute(query, {"group_id": group_id, "user_id": user_id, "server_id": server_id, "license": self._license.resources})
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
                'ssl_ca_certificate': result[0]['ssl_ca_certificate'],
                'ssl_verify_ca': result[0]['ssl_verify_ca']
            }
        }
        return credentials

    def stop(self, user, export_uri):
        query = """
            UPDATE exports
            SET `stop` = 1
            WHERE `user_id` = %s
            AND `uri` = %s
        """
        return self._sql.execute(query, (user['id'], export_uri))

    def update_status(self, user, export_id, status, error=None):
        query = """
            UPDATE exports
            SET
                status = %s,
                error = IF(%s IS NULL, error, %s)
            WHERE id = %s
            AND user_id = %s
        """
        return self._sql.execute(query, (status, error, error, export_id, user['id']))
