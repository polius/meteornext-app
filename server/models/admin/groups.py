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
            INSERT INTO groups (name, description, coins_day, coins_max, coins_execution, deployments_enable, deployments_basic, deployments_pro, deployments_inbenta, deployments_edit, deployments_execution_threads, deployments_execution_plan_factor) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self._mysql.execute(query, (group['name'], group['description'], group['coins_day'], group['coins_max'], group['coins_execution'], group['deployments_enable'], group['deployments_basic'], group['deployments_pro'], group['deployments_inbenta'], group['deployments_edit'], group['deployments_execution_threads'], group['deployments_execution_plan_factor']))

    def put(self, group):
        query = """
            UPDATE groups 
            SET name = %s, 
            description = %s,
            coins_day = %s,
            coins_max = %s,
            coins_execution = %s,
            deployments_enable = %s,
            deployments_basic = %s,
            deployments_pro = %s,
            deployments_inbenta = %s,
            deployments_edit = %s,
            deployments_execution_threads = %s,
            deployments_execution_plan_factor = %s
            WHERE id = %s
        """
        self._mysql.execute(query, (group['name'], group['description'], group['coins_day'], group['coins_max'], group['coins_execution'], group['deployments_enable'], group['deployments_basic'], group['deployments_pro'], group['deployments_inbenta'], group['deployments_edit'], group['deployments_execution_threads'], group['deployments_execution_plan_factor'], group['id']))

    def delete(self, group):
        self._mysql.execute("DELETE FROM groups WHERE name = %s", (group))
    
    def exist(self, group):
        return self._mysql.execute("SELECT EXISTS ( SELECT * FROM groups WHERE name = %s) AS exist", (group['name']))[0]['exist'] == 1
