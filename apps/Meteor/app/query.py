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
    def __init__(self, logger, args, credentials, query_template_js, execution_name, environment_name=None, environment_data=None, sql_connection=None):
        self._logger = logger
        self._args = args
        self._credentials = credentials
        self._query_template = query_template_js
        self._execution_name = execution_name
        self._environment_name = environment_name
        self._environment_data = environment_data
        self._sql_connection = sql_connection

        # Current Server and Database
        self._current_server = None
        self._current_database = None

        # Init Query Template Instance
        self._query_template_instance = query_template(self._query_template)

        # Init MySQL
        if sql_connection is not None:
            self.__init_mysql()

        # Init Execution Log
        self._execution_log = {"output": []}

    @property
    def sql(self):
        return self._sql

    @property
    def credentials(self):
        return self._credentials

    @property
    def execution_log(self):
        return self._execution_log

    def clear_execution_log(self):
        self._execution_log = {"output": []}

    def set_sql_connection(self, server):
        self._sql_connection = server
        self.__init_mysql()

    def __init_mysql(self):
        self._sql = mysql(self._logger, self._args, self._credentials)
        self._sql.connect(self._sql_connection.get('hostname'), self._sql_connection.get('username'), self._sql_connection.get('password'), self._sql_connection.get('database'))

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
        server_sql = self._sql_connection['name'] if auxiliary is None else auxiliary['auxiliary_connection']
        region = self._environment_data['region']

        # SQL Connection and Database
        conn = ''
        if auxiliary is None:
            conn = self._sql
            database_parsed = '__GLOBAL__' if database is None else database
        else:
            aux_credentials = self._credentials['auxiliary_connections'][auxiliary['auxiliary_connection']]
            conn = mysql(self._logger, self._args, self._credentials)
            conn.connect(aux_credentials['hostname'], aux_credentials['username'], aux_credentials['password'])
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

        # If Test Run --> Syntax Checks + Execution Checks
        if not self._args.env_start_deploy:
            # Syntax Checks
            query_syntax = self.get_query_type(query_parsed, show_output=False)
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
                query_info = conn.execute(query_parsed, database_name)
                # If the query is executed successfully, then write the query result to the Log
                execution_row['meteor_output'] = query_info['query_result'] if str(query_info['query_result']) != '()' else '[]'
                # execution_row['meteor_response'] = "Query successfully executed"
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