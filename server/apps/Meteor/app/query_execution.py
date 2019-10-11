#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from collections import OrderedDict

class query_execution:
    def __init__(self, query_instance=None):
        self._meteor = query_instance

        ############################################################################
        # Usage: self._meteor.execute(query=self._queries['1'], database=database) #
        ############################################################################
        self._queries = {
            # '1': "<query>"
        }

        #######################################################################
        # Usage: self._meteor.execute(auxiliary=self._auxiliary_queries['1']) #
        #######################################################################
        self._auxiliary_queries = {
            # '1': {"auxiliary_connection": "<auxiliary_connection_name>", "database": "<database>", "query": "<query>"}
        }

    #######################################################
    # Executed once per Region before all main executions #
    #######################################################
    def before(self, environment, region):
        pass

    ##############################
    # Executed once per Database #
    ##############################
    def main(self, environment, region, server, database):
        pass

    ######################################################
    # Executed once per Region after all main executions #
    ######################################################
    def after(self, environment, region):
        pass

    ########################
    # User Defined Methods #
    ########################
    def __searchInListDict(self, list_dicts, key_name, value_to_find):
        # Search a key value in a list of dictionaries
        return len(filter(lambda obj: obj[key_name] == value_to_find, list_dicts)) > 0

    def __str2dict(self, data):
        # Convert a string representation of a dictionary to a dictionary
        return json.loads(data, object_pairs_hook=OrderedDict)

    def __dict2str(self, data):
        # Convert a dictionary to a string
        return json.dumps(data, separators=(',', ':'))

    #################
    # DO NOT CHANGE #
    #################
    @property
    def queries(self):
        return self._queries

    @property
    def auxiliary_queries(self):
        return self._auxiliary_queries

    def set_query(self, query_instance):
        self._meteor = query_instance