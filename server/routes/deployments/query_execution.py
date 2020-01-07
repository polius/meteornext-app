import json
from collections import OrderedDict

class query_execution:
    def __init__(self):
        #####################################################################
        # Usage: meteor.execute(query=self.queries['1'], database=database) #
        #####################################################################
        self.queries = {
            # '1': "<query>"
        }

        ################################################################
        # Usage: meteor.execute(auxiliary=self.auxiliary_queries['1']) #
        ################################################################
        self.auxiliary_queries = {
            # '1': {"auxiliary_connection": "<auxiliary_connection_name>", "database": "<database>", "query": "<query>"}
        }

    #######################################################
    # Executed once per Region before all main executions #
    #######################################################
    def before(self, meteor, environment, region):
        pass

    ##############################
    # Executed once per Database #
    ##############################
    def main(self, meteor, environment, region, server, database):
        pass

    ######################################################
    # Executed once per Region after all main executions #
    ######################################################
    def after(self, meteor, environment, region):
        pass

    ########################
    # User Defined Methods #
    ########################
    def __searchInListDict(self, list_dicts, key_name, value_to_find):
        # Search a key value in a list of dictionaries
        return [i for i in list_dicts if i[key_name] == value_to_find]

    def __str2dict(self, data):
        # Convert a string representation of a dictionary to a dictionary
        return json.loads(data, object_pairs_hook=OrderedDict)

    def __dict2str(self, data):
        # Convert a dictionary to a string
        return json.dumps(data, separators=(',', ':')).encode('unicode_escape').replace("'","\\'")
