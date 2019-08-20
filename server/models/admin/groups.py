#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Groups:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group=None):
        if group is None:
            return self._mysql.execute("SELECT * FROM groups")
        else:
            return self._mysql.execute("SELECT * FROM groups WHERE name = %s", (group['name']))

    def post(self, group):
        self._mysql.execute("INSERT INTO groups (name, description) VALUES (%s, %s)", (group['name'], group['description']))

    def put(self, group):
        self._mysql.execute("UPDATE groups SET name = %s, description = %s WHERE name = %s", (group['name'], group['description'], group['current_name']))

    def delete(self, group):
        self._mysql.execute("DELETE FROM groups WHERE name = %s", (group))
    
    def exist(self, group):
        return self._mysql.execute("SELECT EXISTS ( SELECT * FROM groups WHERE name = %s) AS exist", (group['name']))[0]['exist'] == 1
