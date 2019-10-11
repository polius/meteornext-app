#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import shutil
from colors import colored

class logs:
    def __init__(self, logger, args, execution_name):
        self._logger = logger
        self._args = args
        self._SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
        self._EXECUTION_NAME = execution_name

        logs_path = self._args.logs_path if self._args.logs_path.endswith('/') else self._args.logs_path + '/'
        self._LOGS_PATH = "{}{}/".format(logs_path, self._EXECUTION_NAME)

    def get_logs_path(self):
        return self._LOGS_PATH

    def generate(self):
        # Create Folder to Store the Logs of the Current Execution
        if not os.path.exists(self._LOGS_PATH + 'execution'):
            os.makedirs(self._LOGS_PATH + 'execution')

        # Copy the 'query_execution.py' file
        if self._args.query_execution_path is not None and not os.path.exists(self._args.query_execution_path):
            raise Exception("The imported query_execution.py using the '--query_execution_path' flag does not exists in: {}".format(self._args.query_execution_path))

        query_execution_file_path = self._SCRIPT_PATH + '/query_execution.py' if self._args.query_execution_path is None else self._args.query_execution_path

        if not os.path.exists(self._LOGS_PATH + 'query_execution.py') and os.path.isfile(query_execution_file_path):
            shutil.copy(query_execution_file_path, self._LOGS_PATH + 'query_execution.py')

        # Copy the 'credentials.json' file
        if self._args.credentials_path is not None and not os.path.exists(self._args.credentials_path):
            raise Exception("The imported credentials.json using the '--credentials_path' flag does not exists in: {}".format(self._args.credentials_path))

        credentials_file_path = self._SCRIPT_PATH + '/credentials.json' if self._args.credentials_path is None else self._args.credentials_path

        if not os.path.exists(self._LOGS_PATH + 'credentials.json') and os.path.isfile(credentials_file_path):
            shutil.copy(credentials_file_path, self._LOGS_PATH + 'credentials.json')

    def compile(self, logs, summary_raw, exception=None):
        try:
            with open(self._LOGS_PATH + 'meteor.js', 'w') as write_file:
                # Write Parsed Data
                write_file.write('var DATA = {};\n'.format(json.dumps(logs, separators=(',', ':'))))
                # Write Sorted Displayed Columns
                write_file.write('var COLUMNS = ["meteor_timestamp", "meteor_environment", "meteor_region", "meteor_server", "meteor_database", "meteor_query", "meteor_status", "meteor_response", "meteor_execution_time", "meteor_output"];\n')
                # Write the Execution Information
                summary = summary_raw
                summary['mode'] = 'deploy' if self._args.deploy else 'test' 
                write_file.write('var INFO = {};\n'.format(json.dumps(summary, separators=(',', ':'))))
                # If there's an Exception, add it to the file
                if exception is not None and not exception.startswith('[QUERY_ERROR]'):
                    parsed_exception = exception.replace('"', '\\"').replace("\n", "\\n")
                    write_file.write('var ERROR = "{}";\n'.format(parsed_exception))
            
        except Exception as e:
            raise Exception('[USER] Error Compiling Meteor Data. ' + str(e))

    def compress(self, compressed_name):
        # Delete query_execution.pyc file
        if os.path.exists(self._LOGS_PATH + 'query_execution.pyc'):
            os.remove(self._LOGS_PATH + 'query_execution.pyc')

        # Tar Gz Deploy Folder
        if self._args.logs_path is None:
            compressed_file_name = "{}/logs/{}".format(self._SCRIPT_PATH, compressed_name)
        else:
            logs_path = self._args.logs_path if self._args.logs_path.endswith('/') else self._args.logs_path + '/'
            compressed_file_name = "{}{}".format(logs_path, compressed_name)

        shutil.make_archive(compressed_file_name, 'gztar', self._LOGS_PATH)
