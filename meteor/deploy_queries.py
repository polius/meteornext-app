import re
import threading
from time import time
from datetime import datetime

from query_template import query_template
from connector import connector

class deploy_queries:
    def __init__(self, args, imports):
        self._args = args
        self._credentials = imports.credentials
        self._query_template = imports.query_template

        # Store Server Credentials + SQL Connection + List of Auxiliary Connections
        self._server = None
        self._sql = None
        self._aux = []

        # Init Query Template Instance
        self._query_template_instance = query_template(self._query_template)

        # Init Execution Log
        self._execution_log = {"output": []}

    @property
    def execution_log(self):
        return self._execution_log

    def clear_execution_log(self):
        self._execution_log = {"output": []}

    def start_sql_connection(self, server):
        self._server = server
        self._sql = connector(server)
        self._sql.start()

    def close_sql_connection(self):
        self._sql.stop()

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
        database_name = database if auxiliary is None else auxiliary['database']
        database_parsed = '' if database is None else database
        query_parsed = self.__parse_query(query) if auxiliary is None else self.__parse_query(auxiliary['query'])
        query_alias = query_parsed if alias is None else '[ALIAS] {}'.format(alias)
        server_sql = self._server['sql']['name'] if auxiliary is None else auxiliary['auxiliary_connection']
        region = self._server['region']

        # SQL Connection
        if auxiliary is None:
            conn = self._sql

        # Auxiliary Connection
        else:
            if auxiliary['auxiliary_connection'] not in self._aux:
                aux = self._credentials['auxiliary_connections'][auxiliary['auxiliary_connection']]
                server = {"ssh": aux['ssh'], "sql": aux['sql']}
                conn = connector(server)
                conn.start()
                self._aux.append({auxiliary['auxiliary_connection']: conn})
            else:
               conn = self._aux[auxiliary['auxiliary_connection']]

        # Init a new Row
        date_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S.%f UTC')
        execution_row = {"meteor_timestamp": date_time, "meteor_environment": self._args.environment, "meteor_region": region, "meteor_server": server_sql, "meteor_database": database_parsed, "meteor_query": query_alias, "meteor_status": "1", "meteor_response": "", "meteor_execution_time": ""}

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
                        raise Exception('[Execution Limit] The total number of scanned items exceeds the maximum dataset size')

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
                # Write Exception to the Log
                execution_row['meteor_status'] = '0'
                execution_row['meteor_response'] = self.__parse_error(str(e))
                self._execution_log['output'].append(execution_row)
                # Do not Raise the Exception. Continue with the Deployment
                if e.__class__ == KeyboardInterrupt:
                    raise

    def __parse_error(self, error):
        return re.sub('\s+', ' ', error.replace('\n', ' ')).strip()