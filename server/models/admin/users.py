#!/usr/bin/env python
# -*- coding: utf-8 -*-
import models.mysql

class Users:
    def __init__(self, credentials):
        self._mysql = models.mysql.mysql(credentials)

    def get(self, username=None):
        if username is None:
            return self._mysql.execute("SELECT u.id, u.username, u.email, u.password, u.coins, u.group_id, g.name AS `group`, u.admin FROM users u JOIN groups g ON g.id = u.group_id")
        else:
            query = """
                SELECT u.id, u.username, u.email, u.password, u.coins, u.group_id, g.name AS `group`, u.admin, g.deployments_enable, g.deployments_basic, g.deployments_pro, g.deployments_inbenta, g.deployments_edit
                FROM users u 
                JOIN groups g ON g.id = u.group_id 
                WHERE u.username = %s
            """
            return self._mysql.execute(query, (username))
    
    def post(self, user):
        self._mysql.execute("INSERT INTO users (username, password, email, coins, group_id, admin) SELECT %s, %s, %s, id, %s FROM groups WHERE name = %s", (user['username'], user['password'], user['email'], user['coins'], user['admin'], user['group']))

    def put(self, user):
        self._mysql.execute("UPDATE users SET username = %s, password = %s, email = %s, coins = %s, admin = %s, group_id = (SELECT id FROM groups WHERE `name` = %s) WHERE username = %s", (user['username'], user['password'], user['email'], user['coins'], user['admin'], user['group'], user['current_username']))

    def put_profile(self, user):
        self._mysql.execute("UPDATE users SET password = %s, email = %s WHERE username = %s", (user['password'], user['email'], user['username']))

    def delete(self, users):
        for user in users:
            self._mysql.execute("DELETE FROM users WHERE username = %s", (user))

    def exist(self, username):
        return self._mysql.execute("SELECT EXISTS ( SELECT * FROM users WHERE username = %s) AS exist", (username))[0]['exist'] == 1

    def is_admin(self, username):
        return len(self._mysql.execute("SELECT admin FROM users WHERE username = '{}' AND admin = 1".format(username))) > 0
    
    def consume_coins(self, user, coins):
        self._mysql.execute("UPDATE users SET coins = coins-%s WHERE username = %s", (coins, user['username']))
