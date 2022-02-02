from datetime import datetime

class Users:
    def __init__(self, sql):
        self._sql = sql

    def get(self, username=None):
        if username is None:
            query = """
                SELECT
                    u.id, u.username, g.name AS `group`, u.email, u.ip, u.user_agent, u2.username AS 'created_by', u.created_at, u3.username AS 'updated_by', u.updated_at, u.last_login, u.coins, u.admin, u.disabled, u.change_password, u.last_ping,
                    CASE
                        WHEN mfa.2fa_hash IS NOT NULL THEN '2fa'
                        WHEN mfa.webauthn_pub_key IS NOT NULL THEN 'webauthn'
                        ELSE NULL
                    END AS 'mfa'
                FROM users u
                LEFT JOIN user_mfa mfa ON mfa.user_id = u.id
                JOIN groups g ON g.id = u.group_id
                LEFT JOIN users u2 ON u2.id = u.created_by
                LEFT JOIN users u3 ON u3.id = u.updated_by
                ORDER BY u.last_login DESC, u.username ASC
            """
            return self._sql.execute(query)
        else:
            query = """
                SELECT
                    u.*,
                    g.name AS `group`,
                    go.user_id IS NOT NULL AS 'owner',
                    g.inventory_enabled, g.inventory_secured, g.deployments_enabled, g.deployments_basic, g.deployments_pro, g.monitoring_enabled, g.utils_enabled, g.client_enabled, g.coins_execution, g.utils_coins, g.coins_day,
                    CASE
                        WHEN mfa.2fa_hash IS NOT NULL THEN '2fa'
                        WHEN mfa.webauthn_pub_key IS NOT NULL THEN 'webauthn'
                        ELSE NULL
                    END AS 'mfa'
                FROM users u
                LEFT JOIN user_mfa mfa ON mfa.user_id = u.id
                JOIN groups g ON g.id = u.group_id
                LEFT JOIN group_owners go ON go.group_id = g.id AND go.user_id = u.id
                WHERE u.username = %s
            """
            return self._sql.execute(query, (username))

    def post(self, user_id, user):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self._sql.execute("INSERT INTO users (username, password, email, coins, group_id, admin, disabled, change_password, created_by, created_at, password_at) SELECT %s, %s, %s, %s, id, %s, %s, %s, %s, %s, %s FROM groups WHERE name = %s", (user['username'], user['password'], user['email'], user['coins'], user['admin'], user['disabled'], user['change_password'], user_id, now, now, user['group']))

    def put(self, user_id, user):
        self._sql.execute("UPDATE users SET username = %s, password = COALESCE(%s, password), email = %s, coins = %s, admin = %s, disabled = %s, change_password = %s, group_id = (SELECT id FROM groups WHERE `name` = %s), updated_by = %s, updated_at = %s WHERE username = %s", (user['username'], user['password'], user['email'], user['coins'], user['admin'], user['disabled'], user['change_password'], user['group'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['current_username']))

    def change_password(self, user):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self._sql.execute("UPDATE users SET password = %s, password_at = %s, change_password = 0 WHERE username = %s", (user['password'], now, user['username']))

    def put_last_login(self, data):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self._sql.execute("UPDATE users SET ip = %s, user_agent = %s, last_login = %s, last_ping = %s WHERE username = %s", (data['ip'], data['user_agent'], now, now, data['username']))

    def put_last_ping(self, user_id):
        self._sql.execute("UPDATE users SET last_ping = %s WHERE id = %s", (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user_id))

    def delete(self, users):
        for user in users:
            self._sql.execute("UPDATE users SET disabled = 1 WHERE username = %s", (user))
            self._sql.execute("DELETE dq FROM deployments_queued dq JOIN executions e ON e.id = dq.execution_id JOIN deployments d ON d.id = e.deployment_id JOIN users u ON u.id = d.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE df FROM deployments_finished df JOIN executions e ON e.id = df.execution_id JOIN deployments d ON d.id = e.deployment_id JOIN users u ON u.id = d.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE dp FROM deployments_pinned dp JOIN users u ON u.id = dp.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE ds FROM deployments_shared ds JOIN users u ON u.id = ds.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE e FROM executions e JOIN deployments d ON d.id = e.deployment_id JOIN users u ON u.id = d.user_id AND u.username = %s", (user))
            self._sql.execute("UPDATE executions JOIN users u ON u.id = executions.user_id AND u.username = %s SET executions.user_id = NULL", (user))
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
            self._sql.execute("DELETE cq FROM client_queries cq JOIN users u ON u.id = cq.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE es FROM environment_servers es JOIN servers s ON s.id = es.server_id AND s.shared = 0 JOIN users u ON u.id = s.owner_id AND u.username = %s", (user))
            self._sql.execute("DELETE s FROM servers s JOIN users u ON u.id = s.owner_id AND u.username = %s WHERE s.shared = 0", (user))
            self._sql.execute("DELETE a FROM auxiliary a JOIN users u ON u.id = a.owner_id AND u.username = %s WHERE a.shared = 0", (user))
            self._sql.execute("DELETE es FROM environment_servers es JOIN environments e ON e.id = es.environment_id AND e.shared = 0 JOIN users u ON u.id = e.owner_id AND u.username = %s", (user))
            self._sql.execute("DELETE e FROM environments e JOIN users u ON u.id = e.owner_id AND u.username = %s WHERE e.shared = 0", (user))
            self._sql.execute("DELETE c FROM cloud c JOIN users u ON u.id = c.owner_id AND u.username = %s WHERE c.shared = 0", (user))
            self._sql.execute("DELETE i FROM `imports` i JOIN users u ON u.id = i.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE e FROM `exports` e JOIN users u ON u.id = e.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE c FROM `clones` c JOIN users u ON u.id = c.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE go FROM group_owners go JOIN users u ON u.id = go.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE mfa FROM user_mfa mfa JOIN users u ON u.id = mfa.user_id WHERE u.username = %s", (user))
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
