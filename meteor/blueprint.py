import json
from collections import OrderedDict

class blueprint:
    def __init__(self):
        ########################################################################################################
        # Usage: meteor.execute(query=self.queries['1'], args=None, database=None, auxiliary=None, alias=None) #
        ########################################################################################################
        self.queries = {
            # '1': "<query>"
        }

    #######################################################
    # Executed once per Server before all main executions #
    #######################################################
    def before(self, meteor, environment, region, server):
        pass

    ##############################
    # Executed once per Database #
    ##############################
    def main(self, meteor, environment, region, server, database):
        pass

    ######################################################
    # Executed once per Server after all main executions #
    ######################################################
    def after(self, meteor, environment, region, server):
        pass

    ########################
    # User Defined Methods #
    ########################
    def search(self, item, key, value):
        # Search a key value in a list of dictionaries
        return [i for i in item if i[key] == value]

    def str2dict(self, data):
        # Convert a string representation of a dictionary to a dictionary
        return json.loads(data, object_pairs_hook=OrderedDict)

    def dict2str(self, data):
        # Convert a dictionary to a string
        return json.dumps(data, separators=(',', ':'))
