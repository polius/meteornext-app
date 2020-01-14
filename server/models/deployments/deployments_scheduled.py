#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Deployments_Scheduled:
    def __init__(self, sql):
        self._sql = sql

    def getBasic(self):
        query = """
            SELECT b.id, d.name, d.user_id, r.name AS 'release', e.name AS 'environment', b.status, CONCAT(TIMEDIFF(b.ended, b.started)) AS 'overall'
            FROM deployments_scheduled s
            JOIN deployments_basic b ON b.id = s.deployment_id AND s.deployment_mode = 'BASIC' AND b.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            JOIN deployments d ON d.id = b.deployment_id
            JOIN releases r ON r.id = d.release_id
            JOIN environments e ON e.id = b.environment_id
        """
        return self._sql.execute(query)

    def getPro(self):
        query = """
            SELECT p.id, d.name, d.user_id, r.name AS 'release', e.name AS 'environment', p.status, CONCAT(TIMEDIFF(p.ended, p.started)) AS 'overall'
            FROM deployments_scheduled s
            JOIN deployments_pro p ON p.id = s.deployment_id AND s.deployment_mode = 'BASIC' AND p.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            JOIN deployments d ON d.id = p.deployment_id
            JOIN releases r ON r.id = d.release_id
            JOIN environments e ON e.id = p.environment_id
        """
        return self._sql.execute(query)

    def getInbenta(self):
        query = """
            SELECT i.id, d.name, d.user_id, r.name AS 'release', e.name AS 'environment', i.status, CONCAT(TIMEDIFF(i.ended, i.started)) AS 'overall'
            FROM deployments_scheduled s
            JOIN deployments_inbenta i ON i.id = s.deployment_id AND s.deployment_mode = 'BASIC' AND i.status IN ('SUCCESS','WARNING','FAILED','STOPPED')
            JOIN deployments d ON d.id = i.deployment_id
            JOIN releases r ON r.id = d.release_id
            JOIN environments e ON e.id = i.environment_id
        """
        return self._sql.execute(query)

    def post(self, deployment):
        self._sql.execute("INSERT INTO deployments_scheduled (deployment_mode, deployment_id) VALUES (%s, %s)", (deployment['mode'], deployment['id']))

    def delete(self, deployment):
        self._sql.execute("DELETE FROM deployments_scheduled WHERE deployment_mode = %s AND deployment_id = %s", (deployment['mode'], deployment['id']))