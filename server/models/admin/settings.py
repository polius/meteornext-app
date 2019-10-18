#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp

class Settings:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, setting_name=None):
        if setting_name:
            query = """
                SELECT name, value
                FROM settings
                WHERE name = %s
            """
            return self._mysql.execute(query, (setting_name))
        else:
            query = """
                SELECT name, value
                FROM settings
            """
            return self._mysql.execute(query)

    def post(self, settings):
        query = """
            INSERT INTO settings (name, value)             
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE value = VALUES(value)
        """
        self._mysql.execute(query, (settings['name'], settings['value']))
