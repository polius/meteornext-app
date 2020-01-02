#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Regions:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id, region_id=None):
        if region_id is None:
            query = """
                SELECT r.*, e.name AS environment
                FROM regions r 
                JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
            """
            return self._sql.execute(query, (group_id))
        else:
            query = """
                SELECT r.*, e.name AS environment
                FROM regions r 
                JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
                WHERE r.id = %s
            """
            return self._sql.execute(query, (group_id, region_id))

    def post(self, group_id, region):
        query = """
            INSERT INTO regions (name, environment_id, cross_region, hostname, port, username, password, `key`, deploy_path)             
            SELECT %s, id, %s , IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s)
            FROM environments
            WHERE group_id = %s AND name = %s
        """
        self._sql.execute(query, (region['name'], region['cross_region'], region['hostname'], region['hostname'], region['port'], region['port'], region['username'], region['username'], region['password'], region['password'], region['key'], region['key'], region['deploy_path'], region['deploy_path'], group_id, region['environment']))

    def put(self, group_id, region):
        query = """
            UPDATE regions
            JOIN environments e ON e.id = regions.environment_id AND e.group_id = %s
            SET regions.name = %s,
                environment_id = (SELECT id FROM environments WHERE name = %s),
                cross_region = %s,
                hostname = IF(%s = '', NULL, %s),
                port = IF(%s = '', NULL, %s),
                username = IF(%s = '', NULL, %s),
                password = IF(%s = '', NULL, %s),
                `key` = IF(%s = '', NULL, %s),
                deploy_path = IF(%s = '', NULL, %s)
            WHERE regions.id = %s
        """
        self._sql.execute(query, (group_id, region['name'], region['environment'], region['cross_region'], region['hostname'], region['hostname'], region['port'], region['port'], region['username'],region['username'], region['password'], region['password'], region['key'], region['key'], region['deploy_path'], region['deploy_path'], region['id']))

    def delete(self, group_id, region_id):
        query = """
            DELETE r
            FROM regions r
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
            WHERE r.id = %s
        """
        self._sql.execute(query, (group_id, region_id))

    def remove(self, group_id):
        query = """
            DELETE r
            FROM regions r
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
        """
        self._sql.execute(query, (group_id))

    def exist(self, group_id, region):
        if 'id' in region:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM regions r
                    JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
                    WHERE r.name = %s
                    AND r.id != %s
                ) AS exist
            """
            return self._sql.execute(query, (group_id, region['environment'], region['name'], region['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM regions r
                    JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
                    WHERE r.name = %s
                ) AS exist
            """
            return self._sql.execute(query, (group_id, region['environment'], region['name']))[0]['exist'] == 1


    def get_by_environment(self, group_id, environment):
        query = """
            SELECT r.name
            FROM regions r 
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
        """
        return self._sql.execute(query, (group_id, environment['name']))

    def get_by_server(self, group_id, server_name):
        query = """
            SELECT r.*
            FROM regions r 
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s 
            WHERE r.name = %s
        """
        return self._sql.execute(query, (group_id, server_name))

    def exist_by_environment(self, group_id, environment):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM regions r
                JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
            ) AS exist
        """
        return self._sql.execute(query, (group_id, environment['name']))[0]['exist'] == 1