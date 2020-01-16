#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

class Settings:
    def __init__(self, sql):
        self._sql = sql

    def get(self, setting_name=None):
        if setting_name:
            query = """
                SELECT name, value
                FROM settings
                WHERE name = %s
            """
            return self._sql.execute(query, (setting_name))
        else:
            query = """
                SELECT name, value
                FROM settings
            """
            return self._sql.execute(query)

    def post(self, user_id, settings):
        query = """
            INSERT INTO settings (name, value, updated_by, updated_at)             
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE value = VALUES(value)
        """
        self._sql.execute(query, (settings['name'], settings['value'], user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
