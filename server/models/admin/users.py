from datetime import datetime

class Users:
    def __init__(self, sql):
        self._sql = sql

    def get(self, username=None):
        if username is None:
            return self._sql.execute("SELECT u.id, u.username, u.email, u.password, u.mfa, u.mfa_hash, u.created_at, u.coins, u.group_id, g.name AS `group`, u.admin, u.last_login FROM users u JOIN groups g ON g.id = u.group_id ORDER BY u.last_login DESC, u.username ASC")
        else:
            query = """
                SELECT u.id, u.username, u.email, u.password, u.mfa, u.mfa_hash, u.created_at, u.coins, u.group_id, g.name AS `group`, u.admin, (go.user_id IS NOT NULL) AS 'owner', u.last_login, g.inventory_enabled, g.inventory_secured, g.deployments_enabled, g.deployments_basic, g.deployments_pro, g.monitoring_enabled, g.utils_enabled, g.client_enabled
                FROM users u 
                JOIN groups g ON g.id = u.group_id
                LEFT JOIN group_owners go ON go.group_id = g.id AND go.user_id = u.id
                WHERE u.username = %s
            """
            return self._sql.execute(query, (username))

    def get_by_id(self, user_id):
        return self._sql.execute("SELECT * FROM users WHERE id = user_id")

    def post(self, user_id, user):
        self._sql.execute("INSERT INTO users (username, password, mfa, email, coins, group_id, admin, created_by, created_at) SELECT %s, %s, %s, %s, %s, id, %s, %s, %s FROM groups WHERE name = %s", (user['username'], user['password'], user['mfa']['enabled'], user['email'], user['coins'], user['admin'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['group']))

    def put(self, user_id, user):
        self._sql.execute("UPDATE users SET username = %s, password = %s, mfa = %s, mfa_hash = %s, email = %s, coins = %s, admin = %s, group_id = (SELECT id FROM groups WHERE `name` = %s), updated_by = %s, updated_at = %s WHERE username = %s", (user['username'], user['password'], user['mfa']['enabled'], user['mfa']['hash'], user['email'], user['coins'], user['admin'], user['group'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user['current_username']))

    def put_profile(self, user):
        self._sql.execute("UPDATE users SET password = %s, mfa = %s, mfa_hash = %s, email = %s WHERE username = %s", (user['password'], user['mfa'], user['mfa_hash'], user['email'], user['username']))

    def put_last_login(self, username):
        self._sql.execute("UPDATE users SET last_login = NOW() WHERE username = %s", (username))

    def delete(self, users):
        for user in users:
            self._sql.execute("DELETE m FROM monitoring m JOIN users u ON u.id = m.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE ms FROM monitoring_settings ms JOIN users u ON u.id = ms.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE csq FROM client_saved_queries csq JOIN users u ON u.id = csq.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE cp FROM client_processlist cp JOIN users u ON u.id = cp.user_id AND u.username = %s", (user))
            self._sql.execute("DELETE FROM users WHERE username = %s", (user))

    def exist(self, username):
        return self._sql.execute("SELECT EXISTS ( SELECT * FROM users WHERE username = %s) AS exist", (username))[0]['exist'] == 1

    def is_admin(self, username):
        return len(self._sql.execute("SELECT admin FROM users WHERE username = '{}' AND admin = 1".format(username))) > 0
    
    def consume_coins(self, user, coins):
        self._sql.execute("UPDATE users SET coins = coins-%s WHERE username = %s", (coins, user['username']))
