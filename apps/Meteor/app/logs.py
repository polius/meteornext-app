#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import shutil
from colors import colored

class logs:
    def __init__(self, logger, args):
        self._logger = logger
        self._args = args
        self._SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

    def generate(self):
        # Create Folder to Store the Logs of the Current Execution
        execution_path = "{}/execution".format(self._args.logs_path)
        if not os.path.exists(execution_path):
            os.makedirs(execution_path)

        # Copy the 'query_execution.py' file
        if self._args.query_execution_path is not None and not os.path.exists(self._args.query_execution_path):
            raise Exception("The imported query_execution.py using the '--query_execution_path' flag does not exists in: {}".format(self._args.query_execution_path))

        query_execution_file_path = self._SCRIPT_PATH + '/query_execution.py' if self._args.query_execution_path is None else self._args.query_execution_path

        if not os.path.exists(self._args.logs_path + '/query_execution.py') and os.path.isfile(query_execution_file_path):
            shutil.copy(query_execution_file_path, self._args.logs_path + '/query_execution.py')

        # Copy the 'credentials.json' file
        if self._args.credentials_path is not None and not os.path.exists(self._args.credentials_path):
            raise Exception("The imported credentials.json using the '--credentials_path' flag does not exists in: {}".format(self._args.credentials_path))

        credentials_file_path = self._SCRIPT_PATH + '/credentials.json' if self._args.credentials_path is None else self._args.credentials_path

        if not os.path.exists(self._args.logs_path + '/credentials.json') and os.path.isfile(credentials_file_path):
            shutil.copy(credentials_file_path, self._args.logs_path + '/credentials.json')

    def compile(self, logs, summary_raw, exception=None):
        try:
            with open(self._args.logs_path + '/meteor.js', 'w') as write_file:
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

    def compress(self):
        # Delete query_execution.pyc file
        if os.path.exists(self._args.logs_path + '/query_execution.pyc'):
            os.remove(self._args.logs_path + '/query_execution.pyc')

        # Tar Gz Deploy Folder
        shutil.make_archive(self._args.logs_path, 'gztar', self._args.logs_path)
