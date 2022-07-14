from datetime import datetime

class Groups:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, group_name=None):
        if group_id is not None:
            return self._sql.execute("SELECT * FROM groups WHERE id = %s", (group_id))
        elif group_name is not None:
            return self._sql.execute("SELECT * FROM groups WHERE name = %s", (group_name))
        else:
            query = """
                SELECT g.id, g.name, g.description, u2.username AS 'created_by', g.created_at, u3.username AS 'updated_by', g.updated_at, COUNT(u.id) AS 'users'
                FROM groups g
                LEFT JOIN users u ON u.group_id = g.id
                LEFT JOIN users u2 ON u2.id = g.created_by
                LEFT JOIN users u3 ON u3.id = g.updated_by
                GROUP BY g.id
            """
            return self._sql.execute(query)

    def post(self, user_id, group):
        query = """
            INSERT INTO groups (name, description, coins_day, coins_max, inventory_enabled, deployments_enabled, deployments_basic, deployments_pro, deployments_coins, deployments_execution_concurrent, deployments_execution_threads, deployments_execution_timeout, deployments_expiration_days, deployments_slack_enabled, deployments_slack_name, deployments_slack_url, monitoring_enabled, monitoring_interval, utils_enabled, utils_coins, utils_limit, utils_concurrent, utils_slack_enabled, utils_slack_name, utils_slack_url, client_enabled, client_limits, client_limits_timeout_mode, client_limits_timeout_value, client_limits_rows, client_tracking, client_tracking_retention, client_tracking_mode, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (group['name'], group['description'], group['coins_day'], group['coins_max'], group['inventory_enabled'], group['deployments_enabled'], group['deployments_basic'], group['deployments_pro'], group['deployments_coins'], group['deployments_execution_concurrent'], group['deployments_execution_threads'], group['deployments_execution_timeout'], group['deployments_expiration_days'], group['deployments_slack_enabled'], group['deployments_slack_name'], group['deployments_slack_url'], group['monitoring_enabled'], group['monitoring_interval'], group['utils_enabled'], group['utils_coins'], group['utils_limit'], group['utils_concurrent'], group['utils_slack_enabled'], group['utils_slack_name'], group['utils_slack_url'], group['client_enabled'], group['client_limits'], group['client_limits_timeout_mode'], group['client_limits_timeout_value'], group['client_limits_rows'], group['client_tracking'], group['client_tracking_retention'], group['client_tracking_mode'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def clone_inventory(self, user_id, source_group_id, target_group_id):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO environments (`name`, `group_id`, `shared`, `created_by`, `created_at`)
            SELECT `name`, %s AS 'group_id', `shared`, %s AS 'created_by', %s AS 'created_at'
            FROM environments
            WHERE `group_id` = %s
            AND `shared` = 1
        """
        self._sql.execute(query, (target_group_id, user_id, now, source_group_id))
        query = """
            INSERT INTO regions (`name`, `group_id`, `ssh_tunnel`, `hostname`, `port`, `username`, `password`, `key`, `shared`, `created_by`, `created_at`)
            SELECT `name`, %s AS 'group_id', `ssh_tunnel`, `hostname`, `port`, `username`, `password`, `key`, `shared`, %s AS 'created_by', %s AS 'created_at'
            FROM regions
            WHERE `group_id` = %s
            AND `shared` = 1
        """
        self._sql.execute(query, (target_group_id, user_id, now, source_group_id))
        query = """
            INSERT INTO servers (`name`, `group_id`, `region_id`, `engine`, `version`, `hostname`, `port`, `username`, `password`, `ssl`, `usage`, `shared`, `created_by`, `created_at`)
            SELECT s.name, %s AS 'group_id', r2.id, s.engine, s.version, s.hostname, s.port, s.username, s.password, s.ssl, s.usage, s.shared, %s AS 'created_by', %s AS 'created_at'
            FROM servers s
            JOIN regions r ON r.id = s.region_id
            JOIN regions r2 ON r2.name = r.name AND r2.group_id = %s
            WHERE s.group_id = %s
            AND s.shared = 1
        """
        self._sql.execute(query, (target_group_id, user_id, now, target_group_id, source_group_id))
        query = """
            INSERT INTO environment_servers (`environment_id`, `server_id`)
            SELECT DISTINCT e2.id AS 'environment_id', s2.id AS 'server_id'
            FROM environment_servers es
            JOIN environments e ON e.id = es.environment_id AND e.group_id = %s AND e.shared = 1
            JOIN servers s ON s.id = es.server_id AND s.group_id = %s AND s.shared = 1
            JOIN environments e2 ON e2.name = e.name AND e2.group_id = %s
            JOIN servers s2 ON s2.name = s.name AND s2.group_id = %s
        """
        self._sql.execute(query, (source_group_id, source_group_id, target_group_id, target_group_id))
        query = """
            INSERT INTO auxiliary (`name`, `group_id`, `engine`, `version`, `hostname`, `port`, `username`, `password`, `ssl`, `shared`, `created_by`, `created_at`)
            SELECT `name`, %s AS 'group_id', `engine`, `version`, `hostname`, `port`, `username`, `password`, `ssl`, `shared`, %s AS 'created_by', %s AS 'created_at'
            FROM auxiliary
            WHERE group_id = %s
            AND shared = 1
        """
        self._sql.execute(query, (target_group_id, user_id, now, source_group_id))
        query = """
            INSERT INTO cloud (`name`, `group_id`, `type`, `access_key`, `secret_key`, `shared`, `created_by`, `created_at`)
            SELECT `name`, %s AS 'group_id', `type`, `access_key`, `secret_key`, `shared`, %s AS 'created_by', %s AS 'created_at'
            FROM cloud
            WHERE group_id = %s
            AND shared = 1
        """
        self._sql.execute(query, (target_group_id, user_id, now, source_group_id))

    def put(self, user_id, group):
        query = """
            UPDATE groups 
            SET name = %s, 
            description = %s,
            coins_day = %s,
            coins_max = %s,
            inventory_enabled = %s,
            deployments_enabled = %s,
            deployments_basic = %s,
            deployments_pro = %s,
            deployments_coins = %s,
            deployments_execution_concurrent = %s,
            deployments_execution_threads = %s,
            deployments_execution_timeout = %s,
            deployments_expiration_days = %s,
            deployments_slack_enabled = %s,
            deployments_slack_name = %s,
            deployments_slack_url = %s,
            monitoring_enabled = %s,
            monitoring_interval = %s,
            utils_enabled = %s,
            utils_coins = %s,
            utils_limit = %s,
            utils_concurrent = %s,
            utils_slack_enabled = %s,
            utils_slack_name = %s,
            utils_slack_url = %s,
            client_enabled = %s,
            client_limits = %s,
            client_limits_timeout_mode = %s,
            client_limits_timeout_value = %s,
            client_limits_rows = %s,
            client_tracking = %s,
            client_tracking_retention = %s,
            client_tracking_mode = %s,
            updated_by = %s,
            updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (group['name'], group['description'], group['coins_day'], group['coins_max'], group['inventory_enabled'], group['deployments_enabled'], group['deployments_basic'], group['deployments_pro'], group['deployments_coins'], group['deployments_execution_concurrent'], group['deployments_execution_threads'], group['deployments_execution_timeout'], group['deployments_expiration_days'], group['deployments_slack_enabled'], group['deployments_slack_name'], group['deployments_slack_url'], group['monitoring_enabled'], group['monitoring_interval'], group['utils_enabled'], group['utils_coins'], group['utils_limit'], group['utils_concurrent'], group['utils_slack_enabled'], group['utils_slack_name'], group['utils_slack_url'], group['client_enabled'], group['client_limits'], group['client_limits_timeout_mode'], group['client_limits_timeout_value'], group['client_limits_rows'], group['client_tracking'], group['client_tracking_retention'], group['client_tracking_mode'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), group['id']))

    def delete(self, group):
        self._sql.execute("UPDATE executions JOIN environments e ON e.id = executions.environment_id AND e.group_id = %s SET executions.environment_id = NULL", (group))
        self._sql.execute("DELETE m FROM monitoring m JOIN servers s ON s.id = m.server_id AND s.group_id = %s", (group))
        self._sql.execute("DELETE me FROM monitoring_events me JOIN servers s ON s.id = me.server_id AND s.group_id = %s", (group))
        self._sql.execute("DELETE ms FROM monitoring_servers ms JOIN servers s ON s.id = ms.server_id AND s.group_id = %s", (group))
        self._sql.execute("DELETE mq FROM monitoring_queries mq JOIN servers s ON s.id = mq.server_id AND s.group_id = %s", (group))
        self._sql.execute("DELETE me FROM monitoring_events me JOIN servers s ON s.id = me.server_id AND s.group_id = %s", (group))
        self._sql.execute("DELETE cs FROM client_servers cs JOIN servers s ON s.id = cs.server_id AND s.group_id = %s", (group))
        self._sql.execute("DELETE i FROM `imports` i JOIN servers s ON s.id = i.server_id AND s.group_id = %s", (group))
        self._sql.execute("DELETE e FROM `exports` e JOIN servers s ON s.id = e.server_id AND s.group_id = %s", (group))
        self._sql.execute("DELETE c FROM `clones` c JOIN servers s ON (s.id = c.source_server OR s.id = c.destination_server) AND s.group_id = %s", (group))
        self._sql.execute("DELETE a FROM auxiliary a WHERE a.group_id = %s", (group))
        self._sql.execute("DELETE es FROM environment_servers es JOIN servers s ON s.id = es.server_id AND s.group_id = %s", (group))
        self._sql.execute("DELETE es FROM environment_servers es JOIN environments e ON e.id = es.environment_id AND e.group_id = %s", (group))
        self._sql.execute("DELETE s FROM servers s WHERE s.group_id = %s", (group))
        self._sql.execute("DELETE r FROM regions r WHERE r.group_id = %s", (group))
        self._sql.execute("DELETE e FROM environments e WHERE e.group_id = %s", (group))
        self._sql.execute("DELETE c FROM cloud c WHERE c.group_id = %s", (group))
        self._sql.execute("DELETE FROM groups WHERE id = %s", (group))

    def exist(self, group):
        if 'id' in group:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM groups 
                    WHERE name = %s
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (group['name'], group['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM groups 
                    WHERE name = %s
                ) AS exist
            """
            return self._sql.execute(query, (group['name']))[0]['exist'] == 1

    def get_owners(self, group_id):
        query = """
            SELECT u.username, u.email, (go.group_id IS NOT NULL) AS 'owner'
            FROM users u
            LEFT JOIN group_owners go ON go.user_id = u.id AND go.group_id = u.group_id
            WHERE u.group_id = %s
        """
        return self._sql.execute(query, (group_id))

    def post_owners(self, group_id, owners):
        for owner in owners:
            query = """
                INSERT IGNORE INTO group_owners (group_id, user_id)
                SELECT %s, id
                FROM users
                WHERE username = %s
            """
            self._sql.execute(query, (group_id, owner))

    def delete_owners(self, group_id, owners):
        for owner in owners:
            query = """
                DELETE go
                FROM group_owners go
                JOIN users u ON u.id = go.user_id AND u.username = %s
                WHERE go.group_id = %s
            """
            self._sql.execute(query, (owner, group_id))

    def get_slack(self, group_id):
        query = """
            SELECT 
                deployments_slack_enabled AS 'enabled', 
                deployments_slack_name AS 'channel_name',
                deployments_slack_url AS 'webhook_url'
            FROM groups
            WHERE id = %s
        """
        return self._sql.execute(query, (group_id))[0]

    def get_usage(self, group_id):
        query = """
            SELECT deployments_enabled, monitoring_enabled, utils_enabled, client_enabled
            FROM groups
            WHERE id = %s
        """
        return self._sql.execute(query, (group_id))[0]

    def get_users(self, group_id):
        query = """
            SELECT *
            FROM users
            WHERE group_id = %s
        """
        return self._sql.execute(query, (group_id))
