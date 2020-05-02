#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

class Slack:
    def __init__(self, sql):
        self._sql = sql

    def get(self, group_id, mode=None):
        if mode:
            query = """
                SELECT mode, channel_name, webhook_url, enabled
                FROM slack
                WHERE group_id = %s
                AND mode = %s
            """
            return self._sql.execute(query, (group_id, mode))
        else:
            query = """
                SELECT mode, channel_name, webhook_url, enabled
                FROM slack
                WHERE group_id = %s
            """
            return self._sql.execute(query, (group_id))

    def post(self, user_id, group_id, slack):
        query = """
            INSERT INTO slack (mode, channel_name, webhook_url, enabled, group_id, created_by, created_at)             
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                channel_name = VALUES(channel_name),
                webhook_url = VALUES(webhook_url),
                enabled = VALUES(enabled),
                updated_by = VALUES(created_by),
                updated_at = VALUES(created_at)
        """
        self._sql.execute(query, (slack['mode'].upper(), slack['channel_name'], slack['webhook_url'], slack['enabled'], group_id, user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def delete(self, group_id):
       self._sql.execute("DELETE FROM slack WHERE group_id = %s", (group_id))
