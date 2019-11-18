#!/usr/bin/env python
# -*- coding: utf-8 -*-
import models.mysql

class Auxiliary:
    def __init__(self, credentials):
        self._mysql = models.mysql.mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT *
            FROM auxiliary
            WHERE group_id = %s
        """
        return self._mysql.execute(query, (group_id))

    def post(self, group_id, auxiliary):
        query = """
            INSERT INTO auxiliary (name, group_id, hostname, username, password)             
            VALUES (%s, %s, %s, %s, %s)
        """
        self._mysql.execute(query, (auxiliary['name'], group_id, auxiliary['hostname'], auxiliary['username'], auxiliary['password']))

    def put(self, group_id, auxiliary):
        query = """
            UPDATE auxiliary
            SET name = %s,
                hostname = %s,
                username = %s,
                password = %s
            WHERE id = %s
            AND group_id = %s
        """
        self._mysql.execute(query, (auxiliary['name'], auxiliary['hostname'], auxiliary['username'], auxiliary['password'], auxiliary['id'], group_id))

    def delete(self, group_id, auxiliary_connection):
        query = """
            DELETE FROM auxiliary
            WHERE name = %s
            AND group_id = %s
        """
        self._mysql.execute(query, (auxiliary_connection['name'], group_id))

    def remove(self, group_id):
        query = """
            DELETE FROM auxiliary
            WHERE group_id = %s
        """
        self._mysql.execute(query, (group_id))

    def exist(self, group_id, auxiliary):
        if 'id' in auxiliary:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM auxiliary
                    WHERE name = %s
                    AND group_id = %s
                    AND id != %s
                ) AS exist
            """
            return self._mysql.execute(query, (auxiliary['name'], group_id, auxiliary['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM auxiliary
                    WHERE name = %s
                    AND group_id = %s
                ) AS exist
            """
            return self._mysql.execute(query, (auxiliary['name'], group_id))[0]['exist'] == 1