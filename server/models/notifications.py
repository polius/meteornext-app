#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Notifications:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id):
        return self._sql.execute("SELECT * FROM notifications WHERE user_id = %s", (user_id))

    def post(self, user_id, notification):
        query = "INSERT INTO notifications (name, icon, category, data, user_id, seen) VALUES (%s, %s, %s, %s, %s, 0)"
        self._sql.execute(query, (notification['name'], notification['icon'], notification['category'], notification['data'], user_id))

    def put(self, user_id, notification):
        self._sql.execute("UPDATE notifications SET seen = 1 WHERE id = %s AND user_id = %s", (notification['id'], user_id))

    def delete(self, user_id, notification):
        self._sql.execute("DELETE FROM notifications WHERE id = %s AND user_id = %s", (notification['id'], user_id))

    def get_unseen(self, user_id):
        return self._sql.execute("SELECT * FROM notifications WHERE seen = 0 AND user_id = %s", (user_id))