#################################################################
# Usage: https://docs.meteornext.io/guides/deployments.html#pro #
#################################################################
import json

class blueprint:
    def __init__(self):
        self.queries = {
            # '1': "<query>"
        }

    #######################################################
    # Executed once per server before all main executions #
    #######################################################
    def before(self, meteor, environment, region, server):
        pass

    ##############################
    # Executed once per database #
    ##############################
    def main(self, meteor, environment, region, server, database):
        pass

    ######################################################
    # Executed once per server after all main executions #
    ######################################################
    def after(self, meteor, environment, region, server):
        pass

    ########################
    # User defined methods #
    ########################
    def search(self, items, key, value):
        # Search a key value in a list of dictionaries
        return [i for i in items if i[key] == value]

    def str2dict(self, data):
        # Convert a string representation of a dictionary to a dictionary
        return json.loads(data)

    def dict2str(self, data):
        # Convert a dictionary to a string
        return json.dumps(data, separators=(',', ':'))
