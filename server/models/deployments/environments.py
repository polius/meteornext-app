#!/usr/bin/env python
# -*- coding: utf-8 -*-
import models.mysql

class Environments:
    def __init__(self, credentials):
        self._mysql = models.mysql.mysql(credentials)

    def get(self, group_id):
        return self._mysql.execute("SELECT * FROM environments WHERE group_id = %s", (group_id))

    def post(self, group_id, environment):
        self._mysql.execute("INSERT INTO environments (name, group_id) VALUES (%s, %s)", (environment['name'], group_id))

    def put(self, group_id, environment):
        self._mysql.execute("UPDATE environments SET name = %s WHERE id = %s AND group_id = %s", (environment['name'], environment['id'], group_id))

    def delete(self, group_id, environment):
        self._mysql.execute("DELETE FROM environments WHERE id = %s AND group_id = %s", (environment['id'], group_id))

    def remove(self, group_id):
        self._mysql.execute("DELETE FROM environments WHERE group_id = %s", (group_id))

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
            return self._mysql.execute(query, (environment['name'], group_id, environment['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM environments 
                    WHERE name = %s 
                    AND group_id = %s
                ) AS exist
            """
            return self._mysql.execute(query, (environment['name'], group_id))[0]['exist'] == 1