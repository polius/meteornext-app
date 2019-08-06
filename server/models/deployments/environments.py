#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Environments:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        return self._mysql.execute("SELECT name FROM environments WHERE group_id = %s", (group_id))

    def post(self, name, group_id):
        self._mysql.execute("INSERT INTO environments (name, group_id) VALUES (%s, %s)", (name, group_id))

    def put(self, current_name, name, group_id):
        self._mysql.execute("UPDATE environments SET name = %s WHERE name = %s AND group_id = %s", (name, current_name, group_id))

    def delete(self, data, group_id):
        for environment in data:
            self._mysql.execute("DELETE FROM environments WHERE name = %s AND group_id = %s", (environment, group_id))

    def exist(self, name, group_id):
        return self._mysql.execute("SELECT EXISTS ( SELECT * FROM environments WHERE name = %s AND group_id = %s) AS exist", (name, group_id))[0]['exist'] == 1