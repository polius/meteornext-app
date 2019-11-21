#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime
from mysql import mysql

class progress:
    def __init__(self, logger, args, credentials, uuid):
        self._args = args
        self._credentials = credentials
        self._uuid = uuid
        self._sql = mysql(logger, args, credentials)
        self._progress = {}
        if self.__enabled():
            self._sql.connect(credentials['meteor_next']['hostname'], credentials['meteor_next']['username'], credentials['meteor_next']['password'], credentials['meteor_next']['database'])

    def start(self, pid):
        if self.__enabled():
            engine = 'amazon_s3' if self._credentials['s3']['enabled'] == 'True' else 'local'
            query = "UPDATE deployments_{} SET status = 'IN PROGRESS', uri = '{}', engine = '{}', started = '{}', pid = '{}' WHERE id = {}".format(self._args.deployment_mode, self._uuid, engine, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pid, self._args.deployment_id)
            self._sql.execute(query, self._credentials['meteor_next']['database'])

    def end(self, execution_status):
        if self.__enabled():
            status = 'SUCCESS' if execution_status == 1 else 'WARNING' if execution_status == 0 else 'STOPPED'
            query = "UPDATE deployments_{} SET status = '{}', ended = '{}', error = 0 WHERE id = {}".format(self._args.deployment_mode, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self._args.deployment_id)
            self._sql.execute(query, self._credentials['meteor_next']['database'])

    def error(self, error_msg):
        if self.__enabled():
            self._progress['error'] = error_msg.replace('"', '\\"').replace("\n", "\\n")
            progress = json.dumps(self._progress).replace("'", "\\\'")
            query = "UPDATE deployments_{} SET status = 'FAILED', progress = '{}', ended = '{}', error = 1 WHERE id = {}".format(self._args.deployment_mode, progress, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self._args.deployment_id)
            self._sql.execute(query, self._credentials['meteor_next']['database'])

    def track_syntax(self, value):
        if self.__enabled():
            if 'syntax' not in self._progress:
                self._progress['syntax'] = []
            self._progress['syntax'].append(value)
            self.__store()

    def track_validation(self, region, value):
        if self.__enabled():
            if 'validation' not in self._progress:
                self._progress['validation'] = {}
            self._progress['validation'][region] = value
            self.__store()
    
    def track_execution(self, value):
        if self.__enabled():
            if 'execution' not in self._progress:
                self._progress['execution'] = {}
            self._progress['execution'] = value
            self.__store()

    def track_logs(self, value):
        if self.__enabled():
            if 'logs' not in self._progress:
                self._progress['logs'] = []
            self._progress['logs'].append(value)
            self.__store()

    def track_tasks(self, value):
        if self.__enabled():
            if 'tasks' not in self._progress:
                self._progress['tasks'] = []
            self._progress['tasks'].append(value)
            self.__store()

    def track_queries(self, value):
        if self.__enabled():
            if 'queries' not in self._progress:
                self._progress['queries'] = {}
            self._progress['queries'] = value
            self.__store()

    def __store(self):
        self._progress['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        progress = json.dumps(self._progress).replace("'", "\\\'")
        query = "UPDATE deployments_{} SET progress = '{}' WHERE id = {}".format(self._args.deployment_mode, progress, self._args.deployment_id)
        self._sql.execute(query, self._credentials['meteor_next']['database'])

    def __enabled(self):
        if 'meteor_next' in self._credentials and self._credentials['meteor_next']['enabled'] == 'True':
            return True
        else:
            return False