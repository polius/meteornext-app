#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class S3:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT aws_access_key, aws_secret_access_key, region_name, bucket_name, enabled
            FROM s3
            WHERE group_id = %s
        """
        return self._mysql.execute(query, (group_id))

    def post(self, group_id, s3):
        query = """
            INSERT INTO s3 (aws_access_key, aws_secret_access_key, region_name, bucket_name, enabled, group_id)             
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self._mysql.execute(query, (s3['aws_access_key'], s3['aws_secret_access_key'], s3['region_name'], s3['bucket_name'], s3['enabled'], group_id))

    def put(self, group_id, s3):
        query = """
            UPDATE s3
            SET aws_access_key = %s,
                aws_secret_access_key = %s,
                region_name = %s,
                bucket_name = %s,
                enabled = %s
            WHERE group_id = %s
        """
        self._mysql.execute(query, (s3['aws_access_key'], s3['aws_secret_access_key'], s3['region_name'], s3['bucket_name'], s3['enabled'], group_id))

    def delete(self, group_id):
       self._mysql.execute("DELETE FROM s3 WHERE group_id = %s", (group_id))

    def exist(self, group_id):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM s3
                WHERE group_id = %s
            ) AS exist
        """
        return self._mysql.execute(query, (group_id))[0]['exist'] == 1