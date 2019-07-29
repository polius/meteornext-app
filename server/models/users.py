#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Users:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def is_admin(self, username):
        data = self._mysql.execute("SELECT admin FROM users WHERE username = '{}' AND admin = 1".format(username))
        return len(data)

    def get(self, group_id=None):
        if group_id is None:
            return self._mysql.execute("SELECT * FROM groups")
        else:
            return self._mysql.execute("SELECT * FROM groups WHERE id = {}".format(group_id))