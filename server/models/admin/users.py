from datetime import datetime

class Users:
    def __init__(self, sql):
        self._sql = sql

    def get(self, username=None):
        if username is None:
            query = """
                SELECT u.id, u.username, u.email, u.password, u.mfa, u.mfa_hash, u.mfa_created, u.created_at, u.coins, u.group_id, g.name AS `group`, u.admin, u.disabled, u.last_login, u.last_ping
                FROM users u
                JOIN groups g ON g.id = u.group_id
                ORDER BY u.last_login DESC, u.username ASC
            """
            return self._sql.execute(query)
        else:
            query = """
                SELECT u.id, u.username, u.email, u.password, u.mfa, u.mfa_hash, u.mfa_created, u.created_at, u.coins, u.group_id, g.name AS `group`, u.admin, u.disabled, (go.user_id IS NOT NULL) AS 'owner', u.last_login, u.last_ping, g.inventory_enabled, g.inventory_secured, g.deployments_enabled, g.deployments_basic, g.deployments_pro, g.monitoring_enabled, g.utils_enabled, g.client_enabled, g.coins_execution, g.coins_day
                FROM users u 
                JOIN groups g ON g.id = u.group_id
                LEFT JOIN group_owners go ON go.group_id = g.id AND go.user_id = u.id
                WHERE u.username = %s
            """
            return self._sql.execute(query, (username))

    def post(self, user_id, user):
        self._sql.execute("INSERT INTO users (username, password, mfa, email, coins, group_id, admin, disabled, created_by, created_at) SELECT %s, %s, %s, %s, %s, id, %s, %s, %s, %s FROM groups WHERE name = %s", (user['username'], user['password'], user['mfa']['enabled'], user['email'], user['coins'], user['admin'], user['disabled'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['group']))

    def put(self, user_id, user):
        self._sql.execute("UPDATE users SET username = %s, password = %s, mfa = %s, mfa_hash = %s, email = %s, coins = %s, admin = %s, disabled = %s, group_id = (SELECT id FROM groups WHERE `name` = %s), updated_by = %s, updated_at = %s WHERE username = %s", (user['username'], user['password'], user['mfa']['enabled'], user['mfa']['hash'], user['email'], user['coins'], user['admin'], user['disabled'], user['group'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['current_username']))

    def change_password(self, user):
        self._sql.execute("UPDATE users SET password = %s WHERE username = %s", (user['password'], user['username']))

    def enable_mfa(self, user):
        self._sql.execute("UPDATE users SET mfa = 1, mfa_hash = %s, mfa_created = %s WHERE username = %s", (user['mfa_hash'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['username']))

    def disable_mfa(self, user):
        self._sql.execute("UPDATE users SET mfa = 0, mfa_hash = NULL, mfa_created = NULL WHERE username = %s", (user['username']))

    def put_last_login(self, username):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self._sql.execute("UPDATE users SET last_login = %s, last_ping = %s WHERE username = %s", (now, now, username))

    def put_last_ping(self, user_id):
        self._sql.execute("UPDATE users SET last_ping = %s WHERE id = %s", (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user_id))

    def delete(self, users):
        for user in users:
            self._sql.execute("UPDATE users SET disabled = 1 WHERE username = %s", (user))
            self._sql.execute("DELETE dq FROM deployments_queued dq JOIN deployments_basic db ON db.id = dq.execution_id AND dq.execution_mode = 'basic' JOIN deployments d ON d.id = db.deployment_id JOIN users u ON u.id = d.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE dq FROM deployments_queued dq JOIN deployments_pro dp ON dp.id = dq.execution_id AND dq.execution_mode = 'pro' JOIN deployments d ON d.id = dp.deployment_id JOIN users u ON u.id = d.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE df FROM deployments_finished df JOIN deployments_basic db ON db.id = df.deployment_id JOIN deployments d ON d.id = db.deployment_id JOIN users u ON u.id = d.user_id AND u.username = %s WHERE df.deployment_mode = 'basic'", (user))
            self._sql.execute("DELETE df FROM deployments_finished df JOIN deployments_pro dp ON dp.id = df.deployment_id JOIN deployments d ON d.id = dp.deployment_id JOIN users u ON u.id = d.user_id AND u.username = %s WHERE df.deployment_mode = 'pro'", (user))
            self._sql.execute("DELETE db FROM deployments_basic db JOIN deployments d ON d.id = db.deployment_id JOIN users u ON u.id = d.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE dp FROM deployments_pro dp JOIN deployments d ON d.id = dp.deployment_id JOIN users u ON u.id = d.user_id AND u.username = %s", (user))
            self._sql.execute("UPDATE deployments_basic JOIN users u ON u.id = deployments_basic.user_id AND u.username = %s SET deployments_basic.user_id = NULL", (user))
            self._sql.execute("UPDATE deployments_pro JOIN users u ON u.id = deployments_pro.user_id AND u.username = %s SET deployments_pro.user_id = NULL", (user))
            self._sql.execute("DELETE d FROM deployments d JOIN users u ON u.id = d.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE r FROM releases r JOIN users u ON u.id = r.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE n FROM notifications n JOIN users u ON u.id = n.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE m FROM monitoring m JOIN users u ON u.id = m.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE ms FROM monitoring_settings ms JOIN users u ON u.id = ms.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE me FROM monitoring_events me JOIN servers s ON s.id = me.server_id JOIN users u ON u.id <=> s.owner_id AND u.username = %s", (user))
            self._sql.execute("DELETE ms FROM monitoring_servers ms JOIN servers s ON s.id = ms.server_id JOIN users u ON u.id <=> s.owner_id AND u.username = %s", (user))
            self._sql.execute("DELETE csq FROM client_saved_queries csq JOIN users u ON u.id = csq.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE cs FROM client_settings cs JOIN users u ON u.id = cs.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE cs FROM client_servers cs JOIN users u ON u.id = cs.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE cf FROM client_folders cf JOIN users u ON u.id = cf.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE es FROM environment_servers es JOIN servers s ON s.id = es.server_id AND s.shared = 0 JOIN users u ON u.id = s.owner_id AND u.username = %s", (user))
            self._sql.execute("DELETE s FROM servers s JOIN users u ON u.id = s.owner_id AND u.username = %s WHERE s.shared = 0", (user))
            self._sql.execute("DELETE a FROM auxiliary a JOIN users u ON u.id = a.owner_id AND u.username = %s WHERE a.shared = 0", (user))
            self._sql.execute("DELETE es FROM environment_servers es JOIN environments e ON e.id = es.environment_id AND e.shared = 0 JOIN users u ON u.id = e.owner_id AND u.username = %s", (user))
            self._sql.execute("DELETE e FROM environments e JOIN users u ON u.id = e.owner_id AND u.username = %s WHERE e.shared = 0", (user))
            self._sql.execute("DELETE go FROM group_owners go JOIN users u ON u.id = go.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE FROM users WHERE username = %s", (user))

    def exist(self, username):
        return self._sql.execute("SELECT EXISTS ( SELECT * FROM users WHERE username = %s) AS exist", (username))[0]['exist'] == 1

    def is_admin(self, username):
        return len(self._sql.execute("SELECT admin FROM users WHERE username = '{}' AND admin = 1".format(username))) > 0
    
    def consume_coins(self, user, coins):
        self._sql.execute("UPDATE users SET coins = coins-%s WHERE username = %s", (coins, user['username']))

    def clean_shared(self, user_id, group):
        self._sql.execute("DELETE m FROM monitoring m JOIN servers s ON s.id = m.server_id AND s.shared = 1 WHERE m.user_id = %s", (user_id))
        self._sql.execute("UPDATE servers SET group_id = (SELECT id FROM groups WHERE name = %s) WHERE shared = 0 AND owner_id = %s", (group, user_id))
        self._sql.execute("UPDATE servers JOIN regions r ON r.id = servers.region_id AND r.shared = 1 SET servers.region_id = NULL WHERE servers.shared = 0 AND servers.owner_id = %s", (user_id))
        self._sql.execute("UPDATE regions SET group_id = (SELECT id FROM groups WHERE name = %s) WHERE shared = 0 AND owner_id = %s", (group, user_id))
        self._sql.execute("UPDATE auxiliary SET group_id = (SELECT id FROM groups WHERE name = %s) WHERE shared = 0 AND owner_id = %s", (group, user_id))
        self._sql.execute("DELETE es FROM environment_servers es JOIN servers s ON s.id = es.server_id AND s.shared = 1 JOIN environments e ON e.id = es.environment_id AND e.shared = 0 AND e.owner_id = %s", (user_id))
        self._sql.execute("UPDATE environments SET group_id = (SELECT id FROM groups WHERE name = %s) WHERE shared = 0 AND owner_id = %s", (group, user_id))
        self._sql.execute("DELETE cs FROM client_servers cs JOIN servers s ON s.id = cs.server_id AND s.shared = 1 WHERE cs.user_id = %s", (user_id))
