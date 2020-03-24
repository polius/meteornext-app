#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

class Slack:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id):
        query = """
            SELECT channel_name, webhook_url, enabled
            FROM slack
            WHERE group_id = %s
        """
        return self._sql.execute(query, (group_id))

    def post(self, user_id, group_id, slack):
        query = """
            INSERT INTO slack (channel_name, webhook_url, enabled, group_id, created_by, created_at)             
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self._sql.execute(query, (slack['channel_name'], slack['webhook_url'], slack['enabled'], group_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put(self, user_id, group_id, slack):
        query = """
            UPDATE slack
            SET channel_name = %s,
                webhook_url = %s,
                enabled = %s,
                updated_by = %s,
                updated_at = %s
            WHERE group_id = %s
        """
        self._sql.execute(query, (slack['channel_name'], slack['webhook_url'], slack['enabled'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), group_id))
    
    def delete(self, group_id):
       self._sql.execute("DELETE FROM slack WHERE group_id = %s", (group_id))

    def exist(self, group_id):
        query = """
            SELECT EXISTS ( 
                SELECT * 
                FROM slack
                WHERE group_id = %s
            ) AS exist
        """
        return self._sql.execute(query, (group_id))[0]['exist'] == 1