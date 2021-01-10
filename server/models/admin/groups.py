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
            return self._sql.execute("SELECT * FROM groups")

    def post(self, user_id, group):
        query = """
            INSERT INTO groups (name, description, coins_day, coins_max, coins_execution, inventory_enabled, inventory_secured, deployments_enabled, deployments_basic, deployments_pro, deployments_execution_threads, deployments_execution_limit, deployments_execution_concurrent, deployments_slack_enabled, deployments_slack_name, deployments_slack_url, monitoring_enabled, utils_enabled, client_enabled, created_by, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._sql.execute(query, (group['name'], group['description'], group['coins_day'], group['coins_max'], group['coins_execution'], group['inventory_enabled'], group['inventory_secured'], group['deployments_enabled'], group['deployments_basic'], group['deployments_pro'], group['deployments_execution_threads'], group['deployments_execution_limit'], group['deployments_execution_concurrent'], group['deployments_slack_enabled'], group['deployments_slack_name'], group['deployments_slack_url'], group['monitoring_enabled'], group['utils_enabled'], group['client_enabled'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group):
        query = """
            UPDATE groups 
            SET name = %s, 
            description = %s,
            coins_day = %s,
            coins_max = %s,
            coins_execution = %s,
            inventory_enabled = %s,
            inventory_secured = %s,
            deployments_enabled = %s,
            deployments_basic = %s,
            deployments_pro = %s,
            deployments_execution_threads = %s,
            deployments_execution_limit = %s,
            deployments_execution_concurrent = %s,
            deployments_slack_enabled = %s,
            deployments_slack_name = %s,
            deployments_slack_url = %s,
            monitoring_enabled = %s,
            utils_enabled = %s,
            client_enabled = %s,
            updated_by = %s,
            updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (group['name'], group['description'], group['coins_day'], group['coins_max'], group['coins_execution'], group['inventory_enabled'], group['inventory_secured'], group['deployments_enabled'], group['deployments_basic'], group['deployments_pro'], group['deployments_execution_threads'], group['deployments_execution_limit'], group['deployments_execution_concurrent'], group['deployments_slack_enabled'], group['deployments_slack_name'], group['deployments_slack_url'], group['monitoring_enabled'], group['utils_enabled'], group['client_enabled'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), group['id']))

    def delete(self, group):
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
