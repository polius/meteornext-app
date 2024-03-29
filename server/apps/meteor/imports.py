import json
import importlib.util

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
        file_path = '{}/config.json'.format(self._args.path)
        with open(file_path) as data_file:
            data = json.load(data_file)
            return data

    def __load_blueprint(self):
        file_path = "{}/blueprint.py".format(self._args.path)
        blueprint = importlib.util.spec_from_file_location("blueprint", file_path).loader.load_module().blueprint()
        return blueprint
