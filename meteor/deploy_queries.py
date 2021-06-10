import re
import threading
from time import time
from datetime import datetime

from query_template import query_template
from connector import connector

class deploy_queries:
    def __init__(self, args, imports, region):
        self._args = args
        self._imports = imports
        self._region = region

        # Store Server Credentials + SQL Connection + List of Auxiliary Connections
        self._server = None
        self._sql = None
        self._aux = {}

        # Store Transaction & Query Error
        self._transaction = False
        self._query_error = False

        # Init Query Template
        self._query_template = query_template()

        # Init Execution Log
        self._execution_log = {"output": []}

    @property
    def transaction(self):
        return self._transaction

    @property
    def execution_log(self):
        return self._execution_log

    def clear_execution_log(self):
        self._execution_log = {"output": []}
        self._query_error = False

    def start_sql_connection(self, server):
        self._server = server
        self._server['timeout'] = self._imports.config['params']['timeout']
        connection = {'sql': self._server}
        self._sql = connector(connection)
        self._sql.start()

    def close_sql_connection(self):
        # Close server connection
        if self._sql:
            self._sql.stop()

        # Close auxiliary connections
        for conn in self._aux.values():
            conn.stop()

    def execute(self, query, args=None, database=None, auxiliary=None, alias=None):
        # Core Variables
        query_parsed = query.strip()
        server_sql = self._server['name'] if auxiliary is None else auxiliary
        region = self._region['name']

        # Get Query Syntax
        query_syntax = self.__get_query_type(query_parsed)

        # Get SQL Connection
        conn = self._sql if auxiliary is None else self.__get_auxiliary(auxiliary)

        # Query Alias
        query_alias = conn.mogrify(query_parsed, args)
        if alias:
            query_alias = '[{}] {}'.format(alias, query_alias)

        # Init a new Row
        date_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S.%f UTC')
        execution_row = {"meteor_timestamp": date_time, "meteor_environment": self._imports.config['params']['environment'], "meteor_region": region, "meteor_server": server_sql, "meteor_database": database, "meteor_query": query_alias, "meteor_status": "1", "meteor_response": "", "meteor_execution_time": "", "meteor_execution_rows": "0"}

        # Set query transaction
        if self._transaction:
            execution_row['transaction'] = True

        # If Test Run --> Syntax Checks + Execution Checks
        if not self._args.deploy:
            # Execution Checks
            try:
                self._query_template.validate_execution(query_parsed, args, conn, database)
                # Write Exception to the Log
                if query_syntax != 'Select':
                    self._execution_log['output'].append(execution_row)

            except Exception as e:
                self._query_error = True
                # Write Exception to the Log
                execution_row['meteor_status'] = '0'
                execution_row['meteor_response'] = self.__parse_error(str(e))
                self._execution_log['output'].append(execution_row)
                return

        # Execute Query (if --deploy or --test with SELECT queries)
        if self._args.deploy or query_syntax == 'Select':
            try:
                # Execute query
                query_prefix = '/*B' + str(self._imports.config['params']['id']) + '*/' if self._imports.config['params']['mode'] == 'basic' else '/*P' + str(self._imports.config['params']['id']) + '*/'
                query_info = conn.execute(query=query_prefix + query_parsed, args=args, database=database)

                # If the query is executed successfully, then write the query result to the Log
                execution_row['meteor_output'] = query_info['query_result'] if str(query_info['query_result']) != '()' else '[]'
                execution_row['meteor_response'] = ""
                execution_row['meteor_execution_time'] = query_info['query_time']
                execution_row['meteor_execution_rows'] = query_info['query_rows_affected']
                self._execution_log['output'].append(execution_row)

                # Return the Execution Result
                return query_info['query_result']

            except (KeyboardInterrupt, Exception) as e:
                self._query_error = True
                # Write Exception to the Log
                execution_row['meteor_status'] = '0'
                execution_row['meteor_response'] = self.__parse_error(str(e))
                self._execution_log['output'].append(execution_row)
                # Do not Raise the Exception. Continue with the Deployment
                if e.__class__ == KeyboardInterrupt:
                    raise

    def begin(self):
        # End the current transaction
        if self._query_error:
            self.rollback()
        else:
            self.commit()

        # Start a new transaction
        self._transaction = True

        # Start server connection transaction
        if self._sql:
            self._sql.begin()

        # Start auxiliary connections transaction
        for conn in self._aux.values():
            conn.begin()

    def commit(self):
        # End current transaction
        self._transaction = False

        # Check existing query errors
        if self._transaction and self._query_error:
            self.rollback()
        else:
            # Commit server connection
            if self._sql:
                self._sql.commit()

            # Initialize query error
            self._query_error = False

            # Commit auxiliary connections
            for conn in self._aux.values():
                conn.commit()

            # Transaction tasks
            for i in self._execution_log['output']:
                if 'transaction' in i:
                    del i['transaction']

    def rollback(self):
        # End current transaction
        self._transaction = False

        # Rollback server connection
        if self._sql:
            self._sql.rollback()

        # Rollback auxiliary connections
        for conn in self._aux.values():
            conn.rollback()

        # Initialize query error
        self._query_error = False

        # Transaction tasks
        for i in self._execution_log['output']:
            if 'transaction' in i and i['meteor_status'] == '1':
                i['meteor_status'] = '2'
                i['meteor_response'] = ''
                del i['transaction']

    def is_error(self):
        return self._query_error

    def __get_auxiliary(self, auxiliary):
        if auxiliary not in self._aux:
            # Check if the auxiliary connection exists
            if auxiliary not in self._imports.config['auxiliary_connections']:
                raise Exception("The auxiliary connection '{}' does not exist".format(auxiliary))
            # Start connecting to the auxiliary connection
            try:
                aux = self._imports.config['auxiliary_connections'][auxiliary]
                aux['sql']['timeout'] = self._imports.config['params']['timeout']
                conn = connector(aux)
                conn.start()
            except Exception as e:
                raise Exception("Auxiliary Connection [{}]: {}".format(auxiliary, str(e)))
            else:
                self._aux[auxiliary] = conn
        return self._aux[auxiliary]

    def __get_query_type(self, query):
        for t in self._query_template.query_template:
            if query.strip().lower().startswith(t["startswith"].lower()) and t["contains"].lower() in query.strip().lower():
                return t['type']
        return False

    def __parse_error(self, error):
        return re.sub('\s+', ' ', error.replace('\n', ' ')).strip()