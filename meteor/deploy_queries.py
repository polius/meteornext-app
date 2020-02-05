import re
import threading
from time import time
from datetime import datetime

from query_template import query_template
from connector import connector

class deploy_queries:
    def __init__(self, args, imports, region):
        self._args = args
        self._credentials = imports.credentials
        self._query_template = imports.query_template
        self._region = region

        # Store Server Credentials + SQL Connection + List of Auxiliary Connections
        self._server = None
        self._sql = None
        self._aux = []

        # Store Transaction vars
        self._transaction = {"enabled": False, "query_error": False}

        # Init Query Template Instance
        self._query_template_instance = query_template(self._query_template)

        # Init Execution Log
        self._execution_log = {"output": []}

    @property
    def execution_log(self):
        return self._execution_log

    @property
    def transaction(self):
        return self._transaction

    def clear_execution_log(self):
        self._execution_log = {"output": []}
        self._transaction = {"enabled": False, "query_error": False}

    def start_sql_connection(self, server):
        self._server = server
        connection = {'ssh': self._region['ssh'], 'sql': server}
        self._sql = connector(connection)
        self._sql.start()

    def close_sql_connection(self):
        # Close server connection
        if self._sql:
            self._sql.stop()

        # Close auxiliary connections
        for i in self._aux:
            list(i.values())[0].stop()

    def __parse_query(self, query):
        return query.strip()

    def get_query_type(self, query, show_output=True):
        parsed_query = self.__parse_query(query)
        for t in self._query_template:
            if parsed_query.lower().startswith(t["startswith"].lower()) and t["contains"].lower() in parsed_query.lower():
                return t['type']
        return False

    def execute(self, query=None, database=None, auxiliary=None, alias=None):
        # Get Current Thread
        current_thread = threading.current_thread()

        # Core Variables
        database_name = auxiliary['database'] if auxiliary is not None else database if database is not None else ''
        query_parsed = self.__parse_query(query) if auxiliary is None else self.__parse_query(auxiliary['query'])
        query_alias = query_parsed if alias is None else '[ALIAS] {}'.format(alias)
        server_sql = self._server['name'] if auxiliary is None else auxiliary['auxiliary_connection']
        region = self._region['region']

        # SQL Connection
        if auxiliary is None:
            conn = self._sql

        # Auxiliary Connection
        else:
            if auxiliary['auxiliary_connection'] not in self._aux:
                # Check if the auxiliary connection exists
                if auxiliary['auxiliary_connection'] not in self._credentials['auxiliary_connections']:
                    raise Exception("- Auxiliary Connection [{}]: This connection name does not exist".format(auxiliary['auxiliary_connection']))
                # Start connecting to the auxiliary connection
                try:
                    aux = self._credentials['auxiliary_connections'][auxiliary['auxiliary_connection']]
                    conn = connector(aux)
                    conn.start()
                except Exception as e:
                    raise Exception("- Auxiliary Connection [{}]: {}".format(auxiliary['auxiliary_connection'], e.args[1]))

                self._aux.append({auxiliary['auxiliary_connection']: conn})
            else:
               conn = self._aux[auxiliary['auxiliary_connection']]

        # Init a new Row
        date_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S.%f UTC')
        execution_row = {"meteor_timestamp": date_time, "meteor_environment": self._args.environment, "meteor_region": region, "meteor_server": server_sql, "meteor_database": database_name, "meteor_query": query_alias, "meteor_status": "1", "meteor_response": "", "meteor_execution_time": ""}

        # Set query transaction
        if self._transaction['enabled']:
            execution_row['transaction'] = True

        # Get Query Syntax
        query_syntax = self.get_query_type(query_parsed, show_output=False)

        # If Test Run --> Syntax Checks + Execution Checks
        if not self._args.deploy:
            # Execution Checks
            try:
                self._query_template_instance.validate_execution(query_parsed, conn, database_name)
                # Write Exception to the Log
                if query_syntax != 'Select':
                    self._execution_log['output'].append(execution_row)

            except Exception as e:
                self._transaction['query_error'] = True
                # Write Exception to the Log
                execution_row['meteor_status'] = '0'
                execution_row['meteor_response'] = self.__parse_error(str(e))
                self._execution_log['output'].append(execution_row)
                return
        
        # Execute Query (if --deploy or --test with SELECT queries)
        if self._args.deploy or query_syntax == 'Select':
            try:
                # Apply the execution plan factor
                if self._args.execution_limit and query_syntax == 'Select':
                    execution_limit = 0
                    explain = conn.execute('EXPLAIN ' + query_parsed, database_name)['query_result']

                    for i in explain:
                        if i['rows'] > execution_limit:
                            execution_limit = i['rows']
  
                    if execution_limit > int(self._args.execution_limit):
                        raise Exception('Maximum number of rows [{}] exceeded. Please use LIMIT along with ORDER BY'.format(self._args.execution_limit))

                # Execute query
                query_info = conn.execute(query_parsed, database_name)
                # If the query is executed successfully, then write the query result to the Log
                execution_row['meteor_output'] = query_info['query_result'] if str(query_info['query_result']) != '()' else '[]'
                execution_row['meteor_response'] = ""
                execution_row['meteor_execution_time'] = query_info['query_time']
                self._execution_log['output'].append(execution_row)

                # Return the Execution Result
                return query_info['query_result']

            except (KeyboardInterrupt, Exception) as e:
                self._transaction['query_error'] = True
                # Write Exception to the Log
                execution_row['meteor_status'] = '0'
                execution_row['meteor_response'] = self.__parse_error(str(e))
                self._execution_log['output'].append(execution_row)
                # Do not Raise the Exception. Continue with the Deployment
                if e.__class__ == KeyboardInterrupt:
                    raise

    def start(self):
        # Init transaction
        self._transaction = {'enabled': True, 'query_error': False}

        # Start server connection transaction
        if self._sql:
            self._sql.begin()

        # Start auxiliary connections transaction
        for i in self._aux:
            list(i.values())[0].begin()

    def commit(self):
        # Check transaction
        if self._transaction['enabled'] and self._transaction['query_error']:
            self.rollback()

        else:
            # Commit server connection
            if self._sql:
                self._sql.commit()

            # Commit auxiliary connections
            for i in self._aux:
                list(i.values())[0].commit()

            # Transaction tasks
            self._transaction['enabled'] = False
            for i in self._execution_log['output']:
                if 'transaction' in i:
                    del i['transaction']

    def rollback(self):
        if self._transaction['enabled']:
            # Rollback server connection
            if self._sql:
                self._sql.rollback()

            # Rollback auxiliary connections
            for i in self._aux:
                list(i.values())[0].rollback()

            # Transaction tasks
            self._transaction['enabled'] = False
            for i in self._execution_log['output']:
                if i['meteor_status'] == '1':
                    i['meteor_status'] = '2'
                    i['meteor_response'] = ''

                if 'transaction' in i:
                    del i['transaction']                

    def __parse_error(self, error):
        return re.sub('\s+', ' ', error.replace('\n', ' ')).strip()