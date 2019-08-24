#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Environments:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        return self._mysql.execute("SELECT name FROM environments WHERE group_id = %s", (group_id))

    def post(self, group_id, environment):
        self._mysql.execute("INSERT INTO environments (name, group_id) VALUES (%s, %s)", (environment['name'], group_id))

    def put(self, group_id, environment):
        self._mysql.execute("UPDATE environments SET name = %s WHERE name = %s AND group_id = %s", (environment['name'], environment['current_name'], group_id))

    def delete(self, group_id, environment):
        print(group_id)
        self._mysql.execute("DELETE FROM environments WHERE name = %s AND group_id = %s", (environment['name'], group_id))

    def remove(self, group_id):
        self._mysql.execute("DELETE FROM environments WHERE group_id = %s", (group_id))

    def exist(self, group_id, environment):
        return self._mysql.execute("SELECT EXISTS ( SELECT * FROM environments WHERE name = %s AND group_id = %s) AS exist", (environment['name'], group_id))[0]['exist'] == 1
