#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

class Environments:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id):
        return self._sql.execute("SELECT * FROM environments WHERE group_id = %s", (group_id))

    def post(self, user_id, group_id, environment):
        self._sql.execute("INSERT INTO environments (name, group_id, created_by, created_at) VALUES (%s, %s, %s, %s)", (environment['name'], group_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group_id, environment):
        self._sql.execute("UPDATE environments SET name = %s, updated_by = %s, updated_at = %s WHERE id = %s AND group_id = %s", (environment['name'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), environment['id'], group_id))

    def delete(self, group_id, environment):
        self._sql.execute("DELETE FROM environments WHERE id = %s AND group_id = %s", (environment['id'], group_id))

    def remove(self, group_id):
        self._sql.execute("DELETE FROM environments WHERE group_id = %s", (group_id))

    def exist(self, group_id, environment):
        if 'id' in environment:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM environments 
                    WHERE name = %s 
                    AND group_id = %s
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (environment['name'], group_id, environment['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM environments 
                    WHERE name = %s 
                    AND group_id = %s
                ) AS exist
            """
            return self._sql.execute(query, (environment['name'], group_id))[0]['exist'] == 1