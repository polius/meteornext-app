#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Groups:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id=None, group_name=None):
        if group_id is not None:
            return self._mysql.execute("SELECT * FROM groups WHERE id = %s", (group_id))
        elif group_name is not None:
            return self._mysql.execute("SELECT * FROM groups WHERE name = %s", (group_name))
        else:
            return self._mysql.execute("SELECT * FROM groups")

    def post(self, group):
        query = """
            INSERT INTO groups (name, description, deployments_enable, deployments_edit) 
            VALUES (%s, %s, %s, %s)
        """
        self._mysql.execute(query, (group['name'], group['description'], group['deployments_enable'], group['deployments_edit']))

    def put(self, group):
        query = """
            UPDATE groups 
            SET name = %s, 
            description = %s,
            deployments_enable = %s,
            deployments_edit = %s
            WHERE id = %s
        """
        self._mysql.execute(query, (group['name'], group['description'], group['deployments_enable'], group['deployments_edit'], group['id']))

    def delete(self, group):
        self._mysql.execute("DELETE FROM groups WHERE name = %s", (group))
    
    def exist(self, group):
        return self._mysql.execute("SELECT EXISTS ( SELECT * FROM groups WHERE name = %s) AS exist", (group['name']))[0]['exist'] == 1
