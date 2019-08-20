#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Servers:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT s.*, e.name AS 'environment', r.name AS 'region' 
            FROM servers s
            JOIN regions r ON r.id = s.region_id
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
        """
        return self._mysql.execute(query, (group_id))

    def post(self, group_id, server):
        query = """
            INSERT INTO servers (name, region_id, hostname, username, password)             
            SELECT %s, r.id, %s, %s, %s
            FROM regions r
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
            WHERE r.name = %s
        """
        self._mysql.execute(query, (server['name'], server['hostname'], server['username'], server['password'], group_id, server['environment'], server['region']))

    def put(self, group_id, server):
        query = """
            UPDATE servers
            JOIN regions r ON r.id = servers.region_id AND r.name = %s
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
            SET servers.name = %s,
                servers.region_id = r.id,
                servers.hostname = %s,
                servers.username = %s,
                servers.password = %s
            WHERE servers.name = %s
        """
        self._mysql.execute(query, (server['region'], group_id, server['environment'], server['name'], server['hostname'], server['username'], server['password'], server['current_name']))

    def delete(self, group_id, servers):
        for server in servers:
            query = """
                DELETE s
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.name = %s
                JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
                WHERE s.name = %s
            """
            self._mysql.execute(query, (server['region'], group_id, server['environment'], server['name']))

    def remove(self, group_id):
        query = """
            DELETE s
            FROM servers s
            JOIN regions r ON r.id = s.region_id
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
        """
        self._mysql.execute(query, (group_id))

    def exist(self, group_id, server):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.name = %s
                JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
                WHERE s.name = %s
            ) AS exist
        """
        return self._mysql.execute(query, (server['region'], group_id, server['environment'], server['name']))[0]['exist'] == 1