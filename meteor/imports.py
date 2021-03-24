import os
import imp
import sys
import json
import traceback
from collections import OrderedDict

class imports:
    def __init__(self, args):
        self._args = args
        self._config = self.__load_config()
        self._blueprint = self.__load_blueprint()

    @property
    def config(self):
        return self._config

    @property
    def blueprint(self):
        return self._blueprint

    ####################
    # Internal Methods #
    ####################
    def __load_config(self):
        try:
            file_path = '{}/config.json'.format(self._args.path)
            if not os.path.isfile(file_path):
                print("The 'config.json' file has not been found in '{}'".format(file_path))
                sys.exit()
            with open(file_path) as data_file:
                data = json.load(data_file, object_pairs_hook=OrderedDict)
                return data
        except Exception:
            print("The 'config.json' file has syntax errors. Please check if it's a valid JSON.")
            sys.exit()

    def __load_blueprint(self):
        try:
            file_path = "{}/blueprint.py".format(self._args.path)
            blueprint = imp.load_source('blueprint', file_path).blueprint()
            return blueprint
        except Exception:
            print("The 'blueprint.py' has syntax errors.\n\n{}".format(traceback.format_exc()))
            sys.exit()
