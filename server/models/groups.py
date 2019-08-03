#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp
import json

class Groups:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self):
        return self._mysql.execute("SELECT * FROM groups")

    def post(self, data):
        self._mysql.execute("INSERT INTO groups (name, description) VALUES (%s, %s)", (data['name'], data['description']))

    def put(self, data):
        self._mysql.execute("UPDATE groups SET name = %s, description = %s WHERE name = %s", (data['name'], data['description'], data['current_name']))

    def delete(self, data):
        for group in data:
            self._mysql.execute("DELETE FROM groups WHERE name = %s", (group))
    
    def exist(self, data):
        return self._mysql.execute("SELECT EXISTS ( SELECT * FROM groups WHERE name = %s) AS exist", (data['name']))[0]['exist'] == 1
