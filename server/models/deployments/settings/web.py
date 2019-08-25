#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Web:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT url
            FROM web
            WHERE group_id = %s
        """
        return self._mysql.execute(query, (group_id))

    def post(self, group_id, web):
        query = """
            INSERT INTO web (url, group_id)             
            VALUES (%s, %s)
        """
        self._mysql.execute(query, (web['url'], group_id))

    def put(self, group_id, web):
        query = """
            UPDATE web
            SET url = %s
            WHERE group_id = %s
        """
        self._mysql.execute(query, (web['url'], group_id))

    def delete(self, group_id):
        self._mysql.execute("DELETE FROM web WHERE group_id = %s", (group_id))

    def exist(self, group_id):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM web
                WHERE group_id = %s
            ) AS exist
        """
        return self._mysql.execute(query, (group_id))[0]['exist'] == 1