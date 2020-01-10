#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Releases:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user_id):
        return self._sql.execute("SELECT * FROM releases WHERE user_id = %s ORDER BY id DESC", (user_id))

    def post(self, user_id, release):
        self._sql.execute("INSERT INTO releases (name, active, user_id) VALUES (%s, %s, %s)", (release['name'], release['active'], user_id))

    def put(self, user_id, release):
        self._sql.execute("UPDATE releases SET name = %s, active = %s WHERE id = %s AND user_id = %s", (release['name'], release['active'], release['id'], user_id))

    def delete(self, user_id, release_id):
        self._sql.execute("DELETE FROM releases WHERE id = %s AND user_id = %s", (release_id, user_id))

    def exist(self, user_id, release):
        if 'id' in release:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM releases 
                    WHERE name = %s 
                    AND user_id = %s
                    AND id != %s
                ) AS exist
            """
            return self._sql.execute(query, (release['name'], user_id, release['id']))[0]['exist'] == 1
        else:
            query = """
                SELECT EXISTS ( 
                    SELECT * 
                    FROM releases 
                    WHERE name = %s 
                    AND user_id = %s
                ) AS exist
            """
            return self._sql.execute(query, (release['name'], user_id))[0]['exist'] == 1

    def getActive(self, user_id):
        return self._sql.execute("SELECT * FROM releases WHERE user_id = %s AND active = 1 ORDER BY id DESC", (user_id))
    
    def putActive(self, user_id, release):
        self._sql.execute("UPDATE releases SET active = %s WHERE id = %s AND user_id = %s", (release['active'], release['id'], user_id))