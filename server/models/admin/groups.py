#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

class Groups:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id=None, group_name=None):
        if group_id is not None:
            return self._sql.execute("SELECT * FROM groups WHERE id = %s", (group_id))
        elif group_name is not None:
            return self._sql.execute("SELECT * FROM groups WHERE name = %s", (group_name))
        else:
            return self._sql.execute("SELECT * FROM groups")

    def post(self, user_id, group):
        query = """
            INSERT INTO groups (name, description, coins_day, coins_max, coins_execution, inventory_enable, deployments_enable, deployments_basic, deployments_pro, deployments_inbenta, deployments_execution_threads, deployments_execution_limit, deployments_execution_concurrent, created_by, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self._sql.execute(query, (group['name'], group['description'], group['coins_day'], group['coins_max'], group['coins_execution'], group['inventory_enable'], group['deployments_enable'], group['deployments_basic'], group['deployments_pro'], group['deployments_inbenta'], group['deployments_execution_threads'], group['deployments_execution_limit'], group['deployments_execution_concurrent'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group):
        query = """
            UPDATE groups 
            SET name = %s, 
            description = %s,
            coins_day = %s,
            coins_max = %s,
            coins_execution = %s,
            inventory_enable = %s,
            deployments_enable = %s,
            deployments_basic = %s,
            deployments_pro = %s,
            deployments_inbenta = %s,
            deployments_execution_threads = %s,
            deployments_execution_limit = %s,
            deployments_execution_concurrent = %s,
            updated_by = %s,
            updated_at = %s
            WHERE id = %s
        """
        self._sql.execute(query, (group['name'], group['description'], group['coins_day'], group['coins_max'], group['coins_execution'], group['inventory_enable'], group['deployments_enable'], group['deployments_basic'], group['deployments_pro'], group['deployments_inbenta'], group['deployments_execution_threads'], group['deployments_execution_limit'], group['deployments_execution_concurrent'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), group['id']))

    def delete(self, group):
        self._sql.execute("DELETE FROM groups WHERE name = %s", (group))
    
    def exist(self, group):
        if 'id' in group:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM groups 
                    WHERE name = %s
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (group['name'], group['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM groups 
                    WHERE name = %s
                ) AS exist
            """
            return self._sql.execute(query, (group['name']))[0]['exist'] == 1
