import re
import csv
import json
import threading
from time import time
from datetime import datetime

from query_template import query_template
from connector import connector

class deploy_queries:
    def __init__(self, args, imports, region, server, mode, thread_id):
        self.__args = args
        self.__imports = imports
        self.__region = region
        self.__server = server
        self.__mode = mode
        self.__thread_id = thread_id
        self.__database = None

        # Current thread
        self.__current_thread = threading.current_thread()

        # Store Server Credentials + SQL Connection + List of Auxiliary Connections
        self.__sql = None
        self.__aux = {}

        # Store Transaction & Query Error
        self.__tx_id = None
        self.__tx_count = 0
        self.__tx_error = False

        # Init Query Template
        self.__query_template = query_template()

    @property
    def database(self):
        return self.__database

    @database.setter
    def database(self, db):
        self.__database = db

    def start_sql_connection(self):
        self.__server['timeout'] = self.__imports.config['params']['timeout']
        connection = {'sql': self.__server}
        self.__sql = connector(connection)
        self.__sql.start()

    def close_sql_connection(self):
        # Close server connection
        if self.__sql:
            self.__sql.stop()

        # Close auxiliary connections
        for conn in self.__aux.values():
            conn.stop()

    def execute(self, query=None, args=None, database=None, auxiliary=None, alias=None, output=True):
        # Check Arguments
        if query is None or type(query) is not str:
            raise Exception('The query argument is mandatory')
        if database is not None and type(database) is not str:
            raise Exception('The database argument is mandatory')
        if auxiliary is not None and type(auxiliary) is not str:
            raise Exception('The auxiliary argument has an invalid format (should be an string)')
        if alias is not None and type(alias) is not str:
            raise Exception('The alias argument has an invalid format (should be an string)')
        if output is not True and output is not False:
            raise Exception('The output argument has an invalid value (should be either True or False)')

        # Core Variables
        query_parsed = query.strip()
        server_sql = self.__server['name'] if auxiliary is None else auxiliary
        region = self.__region['name']

        # Get Query Syntax
        query_syntax = self.__get_query_type(query_parsed)

        # Get SQL Connection
        conn = self.__sql if auxiliary is None else self.__get_auxiliary(auxiliary)

        # Query Alias
        query_alias = conn.mogrify(query_parsed, args)
        if alias:
            query_alias = '[{}] {}'.format(alias, query_alias)

        # Init a new Row
        date_time = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S.%f UTC')
        execution_row = {"meteor_timestamp": date_time, "meteor_environment": self.__imports.config['params']['environment'], "meteor_region": region, "meteor_server": server_sql, "meteor_database": database, "meteor_query": query_alias, "meteor_status": "1", "meteor_response": "", "meteor_execution_time": "", "meteor_execution_rows": "0", "meteor_output": ""}

        # Set query transaction
        if self.__tx_id:
            execution_row['meteor_status'] = self.__tx_id

        # If Test Run --> Syntax Checks + Execution Checks
        if not self.__args.deploy:
            # Execution Checks
            try:
                self.__query_template.validate_execution(query_parsed, args, conn, database)
                # Write Exception to the Log
                if query_syntax not in ['Select','Server_Level.Show']:
                    self.__store_query(execution_row)

            except Exception as e:
                if self.__tx_id:
                    self.__tx_error = True
                # Write Exception to the Log
                execution_row['meteor_status'] = '0'
                execution_row['meteor_response'] = self.__parse_error(str(e))
                self.__store_query(execution_row)
                self.__current_thread.error = True
                return

        # Execute Query (if --deploy or --test with SELECT/SHOW queries)
        if self.__args.deploy or query_syntax in ['Select','Server_Level.Show']:
            try:
                # Execute query
                query_prefix = '/*' + str(self.__imports.config['params']['id']) + '*/'
                query_info = conn.execute(query=query_prefix + query_parsed, args=args, database=database)

                # If the query is executed successfully, then write the query result to the Log
                execution_row['meteor_output'] = query_info['query_result'] if str(query_info['query_result']) != '()' else '[]'
                execution_row['meteor_output'] = json.dumps(execution_row['meteor_output'], default=self.__serializer, separators=(',',':'))

                if not output:
                    execution_row['meteor_output'] = '-'
                execution_row['meteor_response'] = ""
                execution_row['meteor_execution_time'] = conn.last_execution_time
                execution_row['meteor_execution_rows'] = query_info['query_rows_affected']
                self.__store_query(execution_row)

                # Check if query was COMMIT, ROLLBACK, BEGIN or START TRANSACTION
                while query_parsed.endswith(';'):
                    query_parsed = query_parsed[:-1]
                if query_parsed.upper() == 'COMMIT':
                    self.commit()
                elif query_parsed.upper() == 'ROLLBACK':
                    self.rollback()
                elif query_parsed.upper() in ('BEGIN','START TRANSACTION'):
                    self.begin()

                # Return the Execution Result
                return query_info['query_result']

            except (KeyboardInterrupt, Exception) as e:
                if self.__tx_id:
                    self.__tx_error = True
                # Write Exception to the Log
                execution_row['meteor_status'] = '0'
                execution_row['meteor_response'] = self.__parse_error(str(e))
                execution_row['meteor_execution_time'] = conn.last_execution_time
                self.__store_query(execution_row)
                self.__current_thread.error = True
                # Do not Raise the Exception. Continue with the Deployment
                if e.__class__ == KeyboardInterrupt:
                    raise

    def __store_query(self, query):
        # Get execution path
        if self.__mode == 'main':
            execution_log_path = f"{self.__args.path}/execution/{self.__region['id']}/{self.__server['id']}/{self.__database}.csv"
        else:
            execution_log_path = f"{self.__args.path}/execution/{self.__region['id']}/{self.__server['id']}_{self.__mode}.csv"

        # Store query
        with open(execution_log_path, 'a+', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',', quotechar="'", escapechar='\\', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([query['meteor_timestamp'], query['meteor_environment'], query['meteor_region'], query['meteor_server'], query['meteor_database'], query['meteor_query'], query['meteor_status'], query['meteor_response'], query['meteor_execution_time'], query['meteor_execution_rows'], query['meteor_output']])

    def begin(self):
        # End the current transaction
        if self.__tx_id:
            self.rollback()

        # Start a new transaction
        self.__tx_count += 1
        self.__tx_id = f"tx_{self.__thread_id}.{self.__tx_count}"
        self.__tx_error = False

        # Start server connection transaction
        if self.__sql:
            self.__sql.begin()

        # Start auxiliary connections transaction
        for conn in self.__aux.values():
            conn.begin()

    def commit(self):
        # Commit server connection
        if self.__sql:
            self.__sql.commit()

        # Commit auxiliary connections
        for conn in self.__aux.values():
            conn.commit()

        # Get transaction log path
        if self.__mode == 'main':
            transaction_log_path = f"{self.__args.path}/execution/{self.__region['id']}/{self.__server['id']}/{self.__database}_tx.csv"
        else:
            transaction_log_path = f"{self.__args.path}/execution/{self.__region['id']}/{self.__server['id']}_{self.__mode}_tx.csv"

        # Store transaction
        with open(transaction_log_path, 'a+', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([self.__tx_id, 1])

        # Clear current transaction & query error
        self.__tx_id = None
        self.__tx_error = False

    def rollback(self):
        # Rollback server connection
        if self.__sql:
            self.__sql.rollback()

        # Rollback auxiliary connections
        for conn in self.__aux.values():
            conn.rollback()

        # Get transaction log path
        if self.__mode == 'main':
            transaction_log_path = f"{self.__args.path}/execution/{self.__region['id']}/{self.__server['id']}/{self.__database}_tx.csv"
        else:
            transaction_log_path = f"{self.__args.path}/execution/{self.__region['id']}/{self.__server['id']}_{self.__mode}_tx.csv"

        # Store transaction
        with open(transaction_log_path, 'a+', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([self.__tx_id, 0])

        # Clear current transaction & query error
        self.__tx_id = None
        self.__tx_error = False

    def is_error(self):
        return self.__tx_error

    def __get_auxiliary(self, auxiliary):
        if auxiliary not in self.__aux:
            # Check if the auxiliary connection exists
            if auxiliary not in self.__imports.config['auxiliary_connections']:
                raise Exception("The auxiliary connection '{}' does not exist".format(auxiliary))
            # Start connecting to the auxiliary connection
            try:
                aux = self.__imports.config['auxiliary_connections'][auxiliary]
                aux['sql']['timeout'] = self.__imports.config['params']['timeout']
                conn = connector(aux)
                conn.start()
            except Exception as e:
                raise Exception("Auxiliary Connection [{}]: {}".format(auxiliary, str(e)))
            else:
                self.__aux[auxiliary] = conn
        return self.__aux[auxiliary]

    def __get_query_type(self, query):
        for t in self.__query_template.query_template:
            if query.strip().lower().startswith(t["startswith"].lower()) and t["contains"].lower() in query.strip().lower():
                return t['type']
        return False

    def __parse_error(self, error):
        return re.sub('\s+', ' ', error.replace('\n', ' ')).strip()

    def __serializer(self, obj):
        return obj.__str__()
