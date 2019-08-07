#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Slack:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id):
        query = """
            SELECT webhook_url, enabled
            FROM slack
            WHERE group_id = %s
        """
        return self._mysql.execute(query, (group_id))

    def post(self, group_id, slack):
        query = """
            INSERT INTO slack (webhook_url, enabled, group_id)             
            VALUES (%s, %s, %s)
        """
        self._mysql.execute(query, (slack['webhook_url'], slack['enabled'], group_id))

    def put(self, group_id, slack):
        query = """
            UPDATE slack
            SET webhook_url = %s,
                enabled = %s
            WHERE group_id = %s
        """
        self._mysql.execute(query, (slack['webhook_url'], slack['enabled'], group_id))

    def exist(self, group_id):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM slack
                WHERE group_id = %s
            ) AS exist
        """
        return self._mysql.execute(query, (group_id))[0]['exist'] == 1