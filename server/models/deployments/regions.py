#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Regions:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT r.id, r.name, r.environment_id, e.name AS environment, r.cross_region, r.hostname, r.username, r.password, r.key 
            FROM regions r 
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
        """
        return self._mysql.execute(query, (group_id))

    def post(self, group_id, region):
        query = """
            INSERT INTO regions (name, environment_id, cross_region, hostname, username, password, `key`)             
            SELECT %s, id, %s , IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s)
            FROM environments
            WHERE group_id = %s AND name = %s
        """
        self._mysql.execute(query, (region['name'], region['cross_region'], region['hostname'], region['hostname'], region['username'], region['username'], region['password'], region['password'], region['key'], region['key'], group_id, region['environment']))

    def put(self, group_id, region):
        query = """
            UPDATE regions
            JOIN environments e ON e.id = regions.environment_id AND e.group_id = %s AND e.name = %s
            SET regions.name = %s,
                environment_id = e.id,
                cross_region = %s,
                hostname = IF(%s = '', NULL, %s),
                username = IF(%s = '', NULL, %s),
                password = IF(%s = '', NULL, %s),
                `key` = IF(%s = '', NULL, %s)
            WHERE regions.name = %s
        """
        self._mysql.execute(query, (group_id, region['environment'], region['name'], region['cross_region'], region['hostname'], region['hostname'], region['username'],region['username'], region['password'], region['password'], region['key'], region['key'], region['current_name']))

    def delete(self, group_id, regions):
        for region in regions:
            query = """
                DELETE r
                FROM regions r
                JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
                WHERE r.name = %s
            """
            self._mysql.execute(query, (group_id, region['environment'], region['name']))

    def remove(self, group_id):
        query = """
            DELETE r
            FROM regions r
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s
        """
        self._mysql.execute(query, (group_id))

    def exist(self, group_id, region):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM regions r
                JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
                WHERE r.name = %s
            ) AS exist
        """
        return self._mysql.execute(query, (group_id, region['environment'], region['name']))[0]['exist'] == 1

    def get_by_environment(self, group_id, environment_name):
        query = """
            SELECT r.name
            FROM regions r 
            JOIN environments e ON e.id = r.environment_id AND e.group_id = %s AND e.name = %s
        """
        return self._mysql.execute(query, (group_id, environment_name))