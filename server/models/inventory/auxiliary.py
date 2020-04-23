#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

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

    def post(self, user_id, group_id, auxiliary):
        query = """
            INSERT INTO auxiliary (name, group_id, ssh_tunnel, ssh_hostname, ssh_port, ssh_username, ssh_password, ssh_key, sql_engine, sql_hostname, sql_port, sql_username, sql_password, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self._sql.execute(query, (auxiliary['name'], group_id, auxiliary['ssh_tunnel'], auxiliary['ssh_hostname'], auxiliary['ssh_port'], auxiliary['ssh_username'], auxiliary['ssh_password'], auxiliary['ssh_key'], auxiliary['sql_engine'], auxiliary['sql_hostname'], auxiliary['sql_port'], auxiliary['sql_username'], auxiliary['sql_password'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group_id, auxiliary):
        query = """
            UPDATE auxiliary
            SET name = %s,
                ssh_tunnel = %s, 
                ssh_hostname = %s,
                ssh_port = %s, 
                ssh_username = %s, 
                ssh_password = %s, 
                ssh_key = %s, 
                sql_engine = %s, 
                sql_hostname = %s, 
                sql_port = %s, 
                sql_username = %s, 
                sql_password = %s,
                updated_by = %s,
                updated_at = %s
            WHERE id = %s
            AND group_id = %s
        """
        self._sql.execute(query, (auxiliary['name'], auxiliary['ssh_tunnel'], auxiliary['ssh_hostname'], auxiliary['ssh_port'], auxiliary['ssh_username'], auxiliary['ssh_password'], auxiliary['ssh_key'], auxiliary['sql_engine'], auxiliary['sql_hostname'], auxiliary['sql_port'], auxiliary['sql_username'], auxiliary['sql_password'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), auxiliary['id'], group_id))

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