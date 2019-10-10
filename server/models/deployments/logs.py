#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Logs:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT aws_access_key, aws_secret_access_key, region_name, bucket_name, url
            FROM logs
            WHERE group_id = %s
        """
        return self._mysql.execute(query, (group_id))

    def post(self, group_id, logs):
        query = """
            INSERT INTO logs (aws_access_key, aws_secret_access_key, region_name, bucket_name, url, group_id)             
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self._mysql.execute(query, (logs['aws_access_key'], logs['aws_secret_access_key'], logs['region_name'], logs['bucket_name'], logs['url'], group_id))

    def put(self, group_id, logs):
        query = """
            UPDATE logs
            SET aws_access_key = %s,
                aws_secret_access_key = %s,
                region_name = %s,
                bucket_name = %s,
                url = %s
            WHERE group_id = %s
        """
        self._mysql.execute(query, (logs['aws_access_key'], logs['aws_secret_access_key'], logs['region_name'], logs['bucket_name'], logs['url'], group_id))

    def delete(self, group_id):
       self._mysql.execute("DELETE FROM logs WHERE group_id = %s", (group_id))

    def exist(self, group_id):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM logs
                WHERE group_id = %s
            ) AS exist
        """
        return self._mysql.execute(query, (group_id))[0]['exist'] == 1