#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

class Notifications:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id):
        return self._sql.execute("SELECT * FROM notifications WHERE user_id = %s ORDER BY id DESC", (user_id))

    def post(self, user_id, notification):
        query = "INSERT IGNORE INTO notifications (name, `status`, icon, category, data, `date`, user_id, `show`) VALUES (%s, %s, %s, %s, %s, %s, %s, 1)"
        self._sql.execute(query, (notification['name'], notification['status'], notification['icon'], notification['category'], notification['data'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user_id))

    def put(self, user_id, notification):
        self._sql.execute("UPDATE notifications SET `show` = NOT `show` WHERE id = %s AND user_id = %s", (notification['id'], user_id))

    def delete(self, user_id, notification_id):
        self._sql.execute("DELETE FROM notifications WHERE id = %s AND user_id = %s", (notification_id, user_id))

    def get_notification_bar(self, user_id):
        return self._sql.execute("SELECT id, name, icon, `status`, category, data, date FROM notifications WHERE `show` = 1 AND user_id = %s ORDER BY id DESC", (user_id))
    
    def clear(self, user_id):
        self._sql.execute("UPDATE notifications SET `show` = 0 WHERE user_id = %s", (user_id))
