#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Auxiliary:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT name, hostname, username, password
            FROM auxiliary_connections
            WHERE group_id = %s
        """
        return self._mysql.execute(query, (group_id))

    def post(self, group_id, auxiliary):
        query = """
            INSERT INTO auxiliary_connections (name, group_id, hostname, username, password)             
            VALUES (%s, %s, %s, %s, %s)
        """
        self._mysql.execute(query, (auxiliary['name'], group_id, auxiliary['hostname'], auxiliary['username'], auxiliary['password']))

    def put(self, group_id, auxiliary):
        query = """
            UPDATE auxiliary_connections
            SET name = %s,
                hostname = %s,
                username = %s,
                password = %s
            WHERE name = %s
            AND group_id = %s
        """
        self._mysql.execute(query, (auxiliary['name'], auxiliary['hostname'], auxiliary['username'], auxiliary['password'], auxiliary['current_name'], group_id))

    def delete(self, group_id, auxiliary_connections):
        for auxiliary_connection in auxiliary_connections:
            query = """
                DELETE FROM auxiliary_connections
                WHERE name = %s
                AND group_id = %s
            """
            self._mysql.execute(query, (auxiliary_connection['name'], group_id))

    def exist(self, group_id, auxiliary):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM auxiliary_connections
                WHERE name = %s
                AND group_id = %s
            ) AS exist
        """
        return self._mysql.execute(query, (auxiliary['name'], group_id))[0]['exist'] == 1