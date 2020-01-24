#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import sys
from time import time
from datetime import datetime
from colors import colored
from mysql import mysql
from query_template import query_template


class query:
    def __init__(self, logger, args, credentials, query_template_js, environment_name=None, environment_data=None):
        self._logger = logger
        self._args = args
        self._credentials = credentials
        self._query_template = query_template_js
        self._environment_name = environment_name
        self._environment_data = environment_data
        self._sql_credentials = None
        self._sql_connection = None

        # Current Server and Database
        self._current_server = None
        self._current_database = None

        # Init Query Template Instance
        self._query_template_instance = query_template(self._query_template)

        # Init Execution Log
        self._execution_log = {"output": []}

    @property
    def sql_connection(self):
        return self._sql_connection

    @property
    def execution_log(self):
        return self._execution_log

    def clear_execution_log(self):
        self._execution_log = {"output": []}

    def start_sql_connection(self, server):
        self._sql_credentials = server
        self._sql_connection = mysql(self._logger, self._args, self._credentials)
        self._sql_connection.connect(server['hostname'], server['port'], server['username'], server['password'])

    def close_sql_connection(self):
        self._sql_connection.close()

    def __parse_query(self, query):
        return query.strip()

    def get_query_type(self, query, show_output=True):
        parsed_query = self.__parse_query(query)
        for t in self._query_template:
            if parsed_query.lower().startswith(t["startswith"].lower()) and t["contains"].lower() in parsed_query.lower():
                return t['type']
        return False

    def execute(self, query=None, database=None, auxiliary=None, alias=None):
        # Core Variables
        database_name = database if auxiliary is None else auxiliary['database']
        database_parsed = ''
        query_parsed = self.__parse_query(query) if auxiliary is None else self.__parse_query(auxiliary['query'])
        query_alias = query_parsed if alias is None else '[ALIAS] {}'.format(alias)
        server_sql = self._sql_credentials['name'] if auxiliary is None else auxiliary['auxiliary_connection']
        region = self._environment_data['region']

        # SQL Connection and Database
        conn = ''
        if auxiliary is None:
            conn = self._sql_connection
            database_parsed = '__GLOBAL__' if database is None else database
        else:
            aux_credentials = self._credentials['auxiliary_connections'][auxiliary['auxiliary_connection']]
            conn = mysql(self._logger, self._args, self._credentials)
            conn.connect(aux_credentials['hostname'], aux_credentials['port'], aux_credentials['username'], aux_credentials['password'])
            database_parsed = '__GLOBAL__' if auxiliary['database'] is None else auxiliary['database']

        # Init a new Row
        date_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S.%f UTC')
        execution_row = {"meteor_timestamp": date_time, "meteor_environment": self._environment_name, "meteor_region": region, "meteor_server": server_sql, "meteor_database": database_parsed, "meteor_query": query_alias, "meteor_status": "1", "meteor_response": "", "meteor_execution_time": ""}

        # Print Server, Database and Query
        is_auxiliary = '' if auxiliary is None else 'Auxiliary '
        if (self._current_server != server_sql) or (self._current_database != database):
            self._current_server = server_sql
            self._current_database = database
            if self._credentials['execution_mode']['parallel'] != 'True':
                print("------------------------------------------------------")
                print(colored(is_auxiliary + "Server:", 'blue') + ' [' + colored(server_sql, 'magenta') + ']. ' + colored("Database:", 'blue') + ' [' + colored(database_parsed, 'magenta') + ']')
        
        if self._credentials['execution_mode']['parallel'] != 'True':
            print(colored("Query: ", attrs=['bold']) + ' '.join(query_parsed.replace('\n','').split()))

        # Get Query Syntax
        query_syntax = self.get_query_type(query_parsed, show_output=False)

        # If Test Run --> Syntax Checks + Execution Checks
        if not self._args.env_start_deploy:
            # Syntax Checks
            if query_syntax is False:
                exception_message = "Query '{}' has not passed the Syntax Validation".format(query_parsed)
                # Write Exception to the Log
                execution_row['meteor_response'] = exception_message
                self._execution_log['output'].append(execution_row)
                raise Exception(exception_message)

            # Execution Checks
            try:
                self._query_template_instance.validate_execution(query_parsed, conn, database_name)
                # Write Exception to the Log
                if query_syntax != 'Select':
                    self._execution_log['output'].append(execution_row)
                # Print 'Test Succeeded' Message
                if self._credentials['execution_mode']['parallel'] != 'True':
                    print(colored('Test Succeeded', 'green'))

            except Exception as e:
                if self._credentials['execution_mode']['parallel'] != 'True':
                    print(colored('Test Failed: ', 'red', attrs=['bold']) + colored(self.__parse_error(str(e)), 'red'))

                # Write Exception to the Log
                execution_row['meteor_status'] = '0'
                execution_row['meteor_response'] = self.__parse_error(str(e))
                self._execution_log['output'].append(execution_row)
                return
        
        # Execute Query (if --deploy or --test with SELECT queries)
        if self._args.env_start_deploy or query_syntax == 'Select':
            try:
                # Apply the execution plan factor
                if self._args.execution_plan_factor and query_syntax == 'Select':
                    epf = 0
                    explain = conn.execute('EXPLAIN ' + query_parsed, database_name)['query_result']

                    for i in explain:
                        if i['rows'] > epf:
                            epf = i['rows']
  
                    if epf > int(self._args.execution_plan_factor):
                        raise Exception('[Execution Plan Factor] The total number of scanned items exceeds the maximum dataset size')

                # Execute query
                query_info = conn.execute(query_parsed, database_name)
                # If the query is executed successfully, then write the query result to the Log
                execution_row['meteor_output'] = query_info['query_result'] if str(query_info['query_result']) != '()' else '[]'
                execution_row['meteor_response'] = ""
                execution_row['meteor_execution_time'] = query_info['query_time']
                self._execution_log['output'].append(execution_row)
                if self._credentials['execution_mode']['parallel'] != 'True' and self._args.env_start_deploy:
                    print(colored("Query successfully executed", "green"))

                # Return the Execution Result
                return query_info['query_result']

            except (KeyboardInterrupt, Exception) as e:
                # Write Exception to the Log
                execution_row['meteor_status'] = '0'
                execution_row['meteor_response'] = self.__parse_error(str(e))
                self._execution_log['output'].append(execution_row)
                # Do not Raise the Exception. Continue with the Deployment
                if e.__class__ == KeyboardInterrupt:
                    raise

    def __parse_error(self, error):
        return re.sub('\s+', ' ', error.replace('\n', ' ')).strip()