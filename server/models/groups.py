#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp
import json

class Groups:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def get(self, group_id=None):
        if group_id is None:
            return self._mysql.execute("SELECT * FROM groups")
        else:
            return self._mysql.execute("SELECT * FROM groups WHERE id = {}".format(group_id))