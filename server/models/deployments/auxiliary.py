#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Auxiliary:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id, auxiliary_id=None):
        if auxiliary_id is None:
            query = """
                SELECT *
                FROM auxiliary
                WHERE group_id = %s
            """
            return self._sql.execute(query, (group_id))
        else:
            query = """
                SELECT *
                FROM auxiliary
                WHERE group_id = %s
                AND id = %s
            """
            return self._sql.execute(query, (group_id, auxiliary_id))

    def post(self, group_id, auxiliary):
        query = """
            INSERT INTO auxiliary (name, group_id, hostname, port, username, password)             
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self._sql.execute(query, (auxiliary['name'], group_id, auxiliary['hostname'], auxiliary['port'], auxiliary['username'], auxiliary['password']))

    def put(self, group_id, auxiliary):
        query = """
            UPDATE auxiliary
            SET name = %s,
                hostname = %s,
                port = %s,
                username = %s,
                password = %s
            WHERE id = %s
            AND group_id = %s
        """
        self._sql.execute(query, (auxiliary['name'], auxiliary['hostname'], auxiliary['port'], auxiliary['username'], auxiliary['password'], auxiliary['id'], group_id))

    def delete(self, group_id, auxiliary_id):
        query = """
            DELETE FROM auxiliary
            WHERE group_id = %s
            AND id = %s
        """
        self._sql.execute(query, (group_id, auxiliary_id))

    def remove(self, group_id):
        query = """
            DELETE FROM auxiliary
            WHERE group_id = %s
        """
        self._sql.execute(query, (group_id))

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
            return self._sql.execute(query, (auxiliary['name'], group_id, auxiliary['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM auxiliary
                    WHERE name = %s
                    AND group_id = %s
                ) AS exist
            """
            return self._sql.execute(query, (auxiliary['name'], group_id))[0]['exist'] == 1