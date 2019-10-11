#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Logs:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT mode, data
            FROM logs
            WHERE group_id = %s
        """
        return self._mysql.execute(query, (group_id))

    def post(self, group_id, logs):
        query = """
            INSERT INTO logs (mode, data, group_id)             
            VALUES (%s, %s, %s)
        """
        self._mysql.execute(query, (logs['mode'], logs['data'], group_id))

    def put(self, group_id, logs):
        query = """
            UPDATE logs
            SET mode = %s,
                data = %s
            WHERE group_id = %s
        """
        self._mysql.execute(query, (logs['mode'], logs['data'], group_id))

    def delete(self, group_id):
       self._mysql.execute("DELETE FROM logs WHERE group_id = %s", (group_id))

    def exist(self, group_id):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM logs
                WHERE group_id = %s
            ) AS exist
        """
        return self._mysql.execute(query, (group_id))[0]['exist'] == 1