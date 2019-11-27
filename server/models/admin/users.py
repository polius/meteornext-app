#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Users:
    def __init__(self, sql):
        self._sql = sql

    def get(self, username=None):
        if username is None:
            return self._sql.execute("SELECT u.id, u.username, u.email, u.password, u.coins, u.group_id, g.name AS `group`, u.admin FROM users u JOIN groups g ON g.id = u.group_id")
        else:
            query = """
                SELECT u.id, u.username, u.email, u.password, u.coins, u.group_id, g.name AS `group`, u.admin, g.deployments_enable, g.deployments_basic, g.deployments_pro, g.deployments_inbenta, g.deployments_edit
                FROM users u 
                JOIN groups g ON g.id = u.group_id 
                WHERE u.username = %s
            """
            return self._sql.execute(query, (username))
    
    def post(self, user):
        self._sql.execute("INSERT INTO users (username, password, email, coins, group_id, admin) SELECT %s, %s, %s, id, %s FROM groups WHERE name = %s", (user['username'], user['password'], user['email'], user['coins'], user['admin'], user['group']))

    def put(self, user):
        self._sql.execute("UPDATE users SET username = %s, password = %s, email = %s, coins = %s, admin = %s, group_id = (SELECT id FROM groups WHERE `name` = %s) WHERE username = %s", (user['username'], user['password'], user['email'], user['coins'], user['admin'], user['group'], user['current_username']))

    def put_profile(self, user):
        self._sql.execute("UPDATE users SET password = %s, email = %s WHERE username = %s", (user['password'], user['email'], user['username']))

    def delete(self, users):
        for user in users:
            self._sql.execute("DELETE FROM users WHERE username = %s", (user))

    def exist(self, username):
        return self._sql.execute("SELECT EXISTS ( SELECT * FROM users WHERE username = %s) AS exist", (username))[0]['exist'] == 1

    def is_admin(self, username):
        return len(self._sql.execute("SELECT admin FROM users WHERE username = '{}' AND admin = 1".format(username))) > 0
    
    def consume_coins(self, user, coins):
        self._sql.execute("UPDATE users SET coins = coins-%s WHERE username = %s", (coins, user['username']))
