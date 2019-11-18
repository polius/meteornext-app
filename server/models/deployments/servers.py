#!/usr/bin/env python
# -*- coding: utf-8 -*-
import models.mysql

class Servers:
    def __init__(self, credentials):
        self._mysql = models.mysql.mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT s.*, e.id AS 'environment_id', e.name AS 'environment', r.id AS 'region_id', r.name AS 'region' 
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
            WHERE servers.id = %s
        """
        self._mysql.execute(query, (server['region'], group_id, server['environment'], server['name'], server['hostname'], server['username'], server['password'], server['id']))

    def delete(self, group_id, server):
        query = """
            DELETE s
            FROM servers s
            JOIN regions r ON r.id = s.region_id
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
            WHERE s.id = %s
        """
        self._mysql.execute(query, (group_id, server['id']))

    def remove(self, group_id):
        query = """
            DELETE s
            FROM servers s
            JOIN regions r ON r.id = s.region_id
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
        """
        self._mysql.execute(query, (group_id))

    def exist(self, group_id, server):
        if 'id' in server:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM servers s
                    JOIN regions r ON r.id = s.region_id AND r.name = %s
                    JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
                    WHERE s.name = %s AND s.id != %s
                ) AS exist
            """
            return self._mysql.execute(query, (server['region'], group_id, server['environment'], server['name'], server['id']))[0]['exist'] == 1
        else:
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

    def exist_by_region(self, group_id, region):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM servers s
                JOIN regions r ON r.id = s.region_id AND r.name = %s
                JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
            ) AS exist
        """
        return self._mysql.execute(query, (region['name'], group_id))[0]['exist'] == 1