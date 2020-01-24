import os
import imp
import sys
import json
from collections import OrderedDict

class imports:
    def __init__(self, args):
        self._args = args
        self._SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__)) 

        # Import files
        self._credentials = self.__load_credentials()
        self._query_template = self.__load_query_template()
        self._query_execution = self.__load_query_execution()

    ###########
    # Getters #
    ###########
    @property
    def credentials(self):
        return self._credentials

    @property
    def query_template(self):
        return self._query_template

    @property
    def query_execution(self):
        return self._query_execution

    ####################
    # Internal Methods #
    ####################
    def __load_credentials(self):
        try:
            file_path = '{}/credentials.json'.format(self._args.execution_path)
            if not os.path.isfile(file_path):
                print("The 'credentials.json' file has not been found in '{}'".format(file_path))
                sys.exit()

            with open(file_path) as data_file:
                data = json.load(data_file, object_pairs_hook=OrderedDict)
                return data

        except Exception:
            print("The 'credentials.json' file has syntax errors. Please check if it's a valid JSON.")
            sys.exit()

    def __load_query_execution(self):
        file_path = "{}/query_execution.py".format(self._args.execution_path)
        # Check if query_execution exists
        if not os.path.isfile(file_path):
            error_msg = "The 'query_execution.py' has not been found in '{}'".format(file_path)
            print(error_msg)
            self._progress.error(error_msg)
            sys.exit()

        # Check if query_execution is correctly parsed
        try:
            query_execution = imp.load_source('query_execution', file_path).query_execution()
            return query_execution
        except Exception:
            print("An error has been detected in Pro Code\n\n{}".format(traceback.format_exc()))
            sys.exit()

    def __load_query_template(self):
        try:
            file_path = '{}/query_template.json'.format(self._SCRIPT_PATH)
            with open(file_path) as data_file:
                data = json.load(data_file, object_pairs_hook=OrderedDict)
                return data

        except Exception:
            print("The 'query_template.json' file has syntax errors. Please check if it's a valid JSON.")
            sys.exit()