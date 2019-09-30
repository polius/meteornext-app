#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime
from mysql import mysql

class progress:
    def __init__(self, logger, args, credentials):
        self._args = args
        self._credentials = credentials
        self._sql = mysql(logger, args, credentials)
        self._sql.connect(credentials['meteor_next']['hostname'], credentials['meteor_next']['username'], credentials['meteor_next']['password'], credentials['meteor_next']['database'])
        self._progress = {"validation":{}, "execution":{}, "logs":[], "tasks":[], "queries":{}}

    def start(self):
        if self.__enabled():
            query = "UPDATE deployments_{} SET status = 'IN PROGRESS', started = '{}' WHERE id = {}".format(self._args.deployment_mode, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self._args.deployment_id)
            self._sql.execute(query, self._credentials['meteor_next']['database'])

    def end(self, status, logs_path=None, logs_url=None):
        if self.__enabled():
            if logs_url:
                query = "UPDATE deployments_{} SET logs_path = '{}', logs_url = '{}', status = '{}', ended = '{}', error = 0 WHERE id = {}".format(self._args.deployment_mode, logs_path, logs_url, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self._args.deployment_id)
            elif logs_path:
                query = "UPDATE deployments_{} SET logs_path = '{}', status = '{}', ended = '{}', error = 0 WHERE id = {}".format(self._args.deployment_mode, logs_path, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self._args.deployment_id)
            else:
                query = "UPDATE deployments_{} SET status = '{}', ended = '{}', error = 0 WHERE id = {}".format(self._args.deployment_mode, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self._args.deployment_id)
            self._sql.execute(query, self._credentials['meteor_next']['database'])

    def error(self, error_msg):
        if self.__enabled():
            self._progress['error'] = error_msg.replace('"', '\\"')
            progress = json.dumps(self._progress).replace("'", "\\\'")
            query = "UPDATE deployments_{} SET status = 'FAILED', progress = '{}', ended = '{}', error = 1 WHERE id = {}".format(self._args.deployment_mode, progress, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self._args.deployment_id)
            self._sql.execute(query, self._credentials['meteor_next']['database'])

    def track_validation(self, region, value):
        if self.__enabled():
            self._progress['validation'][region] = value
            self.__store()
    
    def track_execution(self, value):
        if self.__enabled():
            self._progress['execution'] = value
            self.__store()

    def track_logs(self, value):
        if self.__enabled():
            self._progress['logs'].append(value)
            self.__store()

    def track_tasks(self, value):
        if self.__enabled():
            self._progress['tasks'].append(value)
            self.__store()

    def track_queries(self, value):
        if self.__enabled():
            self._progress['queries'] = value
            self.__store()

    def __store(self):
        self._progress['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        progress = json.dumps(self._progress).replace("'", "\\\'")
        query = "UPDATE deployments_{} SET progress = '{}' WHERE id = {}".format(self._args.deployment_mode, progress, self._args.deployment_id)
        self._sql.execute(query, self._credentials['meteor_next']['database'])

    def __enabled(self):
        if self._args.deployment_id is not None and self._args.deployment_mode is not None:
            return True
        else:
            return False