#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Users:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, username=None):
        if username is None:
            return self._mysql.execute("SELECT u.id, u.username, u.email, u.password, g.name AS `group`, u.admin FROM users u JOIN groups g ON g.id = u.group_id")
        else:
            return self._mysql.execute("SELECT u.id, u.username, u.email, u.password, g.name AS `group`, u.admin FROM users u JOIN groups g ON g.id = u.group_id WHERE username = %s", (username))
    
    def post(self, data):
        self._mysql.execute("INSERT INTO users (username, password, email, group_id, admin) SELECT %s, %s, %s, id, %s FROM groups WHERE name = %s", (data['username'], data['password'], data['email'], data['admin'], data['group']))

    def put(self, data):
        self._mysql.execute("UPDATE users SET username = %s, password = %s, email = %s, group_id = %s, admin = %s WHERE username = %s", (data['username'], data['password'], data['email'], data['group_id'], data['admin'], data['username']))

    def delete(self, data):
        for user in data:
            self._mysql.execute("DELETE FROM userns WHERE username = %s", (user))

    def exist(self, username):
        return self._mysql.execute("SELECT EXISTS ( SELECT * FROM users WHERE username = %s) AS exist", (username))[0]['exist'] == 1

    def is_admin(self, username):
        return len(self._mysql.execute("SELECT admin FROM users WHERE username = '{}' AND admin = 1".format(username))) > 0