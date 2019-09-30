#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymysql
import warnings
from time import time
from colors import colored
from collections import OrderedDict
from pymysql.cursors import DictCursorMixin, Cursor

class OrderedDictCursor(DictCursorMixin, Cursor):
    dict_type = OrderedDict

class mysql:
    def __init__(self, logger, args, credentials):
        self._logger = logger
        self._args = args
        self._credentials = credentials
        self._connection = None
        self._mysql = {}

    def connect(self, hostname, username, password, database=None):
        # Store the Credentials
        self._mysql = {"hostname": hostname, "username": username, "password": password, "database": database}

        # Init Connection
        self.__connect(database)

    def __connect(self, database=None):
        if database is not None:
            self._connection = pymysql.connect(host=self._mysql['hostname'], user=self._mysql['username'], password=self._mysql['password'], db=database, charset='utf8mb4', use_unicode=False, cursorclass=pymysql.cursors.DictCursor, autocommit=False)
        else:
            self._connection = pymysql.connect(host=self._mysql['hostname'], user=self._mysql['username'], password=self._mysql['password'], charset='utf8mb4', use_unicode=False, cursorclass=pymysql.cursors.DictCursor, autocommit=False)

    def execute(self, query, database_name=None):
        try:
            try:
                # Establish the Connection
                self.__connect(database_name)

                # Prepare the cursor
                with self._connection.cursor(OrderedDictCursor) as cursor:            
                    # Execute the SQL query ignoring warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        start_time = time()
                        cursor.execute(query)

                    # Get the query results
                    query_result = cursor.fetchall()

                # Commit the changes in the database
                self._connection.commit()
                end_time = time()

                # Return query results
                return { "query_result": query_result, "query_time": "{0:.3f}".format(end_time - start_time) }

            except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
                raise Exception(error.args[1])

        except Exception as e:
            if self._args.env_start_deploy:
                show_output = self._credentials['execution_mode']['parallel'] == "False"
                try:
                    if show_output:
                        print(colored("Error: ", 'red', attrs=['bold']) + colored(colored(e, 'red')))
                        print(colored("--> Rollback Initiated...", 'yellow'))
                    self._connection.rollback()
                    if show_output:
                        print(colored("--> Rollback successfully performed.", 'green'))
                except Exception as e2:
                    if show_output:
                        print(colored("--> Rollback not performed. Error: {}".format(e2), 'red'))
            raise e

        except KeyboardInterrupt:
            if self._args.env_start_deploy:
                show_output = self._credentials['execution_mode']['parallel'] == "False"
                try:
                    if show_output:
                        print(colored("\n--> Rollback Initiated...", 'yellow'))
                    self._connection.rollback()
                    if show_output:
                        print(colored("--> Rollback successfully performed.", 'green'))
                except Exception as e:
                    if show_output:
                        print(colored("--> Rollback not performed. Error: {}".format(e), 'red'))
            raise KeyboardInterrupt("Program Interrupted by User. Rollback successfully performed.")

        finally:
            # Close PyMySQL Connection
            if self._connection is not None and self._connection.open:
                self._connection.close()

    def get_all_databases(self):
        query = "SHOW DATABASES"
        result = self.execute(query)['query_result']

        databases = []
        for db in result:
            databases.append(db['Database'])
        return databases

    def get_databases(self, db_regex):
        query = "SELECT DISTINCT(table_schema) AS table_schema FROM information_schema.tables WHERE table_schema LIKE '" + db_regex.strip() + "'"
        result = self.execute(query)['query_result']

        databases = []
        for db in result:
            databases.append(db['table_schema'])
        return databases

    def get_table_size(self, db, table):
        query = "SELECT (data_length + index_length)/1024/1024 AS table_size FROM information_schema.tables WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\""
        result = self.execute(query)['query_result']
        return result[0]['table_size']

    def check_db_exists(self, db):
        query = "SELECT COUNT(*) AS count FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = \"" + db.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_table_exists(self, db, table):
        query = "SELECT COUNT(*) AS count FROM information_schema.tables WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_column_exists(self, db, table, column):
        query = "SELECT COUNT(*) AS count FROM information_schema.columns WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND column_name = \"" + column.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_index_exists(self, db, table, index):
        query = "SELECT COUNT(*) AS count FROM information_schema.statistics WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND index_name = \"" + index.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) > 0 else False

    def check_pk_exists(self, db, table):
        query = "SELECT COUNT(*) AS count FROM information_schema.statistics WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND index_name = \"PRIMARY\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) >= 1 else False

    def check_pk_exists_columns(self, db, table, columns):
        query = """
            SELECT EXISTS
	        (
                SELECT *
                FROM information_schema.statistics 
                WHERE table_schema = '{}'
                AND table_name = '{}'
                AND column_name IN ({})
                AND index_name = 'PRIMARY'
                GROUP BY table_schema, table_name
                HAVING COUNT(*) = {}
            ) AS exist;
            """.format(db, table, str(columns)[1:-1], len(columns))
        result = self.execute(query)['query_result']
        return True if int(result[0]['exist']) == 1 else False

    def check_fk_exists(self, db, table, column):
        query = "SELECT COUNT(*) AS count FROM information_schema.key_column_usage WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND column_name = \"" + column.strip() + "\" AND referenced_table_name IS NOT NULL"
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_fk_exists_by_name(self, db, table, foreign):
        query = "SELECT COUNT(*) AS count FROM information_schema.key_column_usage WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND constraint_name = \"" + foreign.strip() + "\" AND referenced_table_name IS NOT NULL"
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_partition_exists(self, db, table, partition):
        query = "SELECT COUNT(*) AS count FROM information_schema.partitions WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\" AND partition_name = \"" + partition.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_trigger_exists(self, db, table, trigger):
        query = "SELECT COUNT(*) AS count FROM information_schema.triggers WHERE event_object_schema = \"" + db.strip() + "\" AND event_object_table LIKE \"" + table.strip() + "\" AND trigger_name = \"" + trigger.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_view_exists(self, db, view):
        query = "SELECT COUNT(*) AS count FROM information_schema.views WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + view.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_function_exists(self, db, function):
        query = "SELECT COUNT(*) AS count FROM information_schema.routines WHERE routine_schema = \"" + db.strip() + "\" AND routine_name = \"" + function.strip() + "\" AND routine_type = \"FUNCTION\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_procedure_exists(self, db, procedure):
        query = "SELECT COUNT(*) AS count FROM information_schema.routines WHERE routine_schema = \"" + db.strip() + "\" AND routine_name = \"" + procedure.strip() + "\" AND routine_type = \"PROCEDURE\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_event_exists(self, event):
        query = "SELECT COUNT(*) AS count FROM information_schema.events WHERE EVENT_NAME = \"" + event.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def check_user_exists(self, user, host):
        query = "SELECT COUNT(*) AS count FROM mysql.user WHERE User = \"" + user + "\" AND Host = \"" + host.strip() + "\""
        result = self.execute(query)['query_result']
        return True if int(result[0]['count']) == 1 else False

    def get_row_format(self, db, table):
        query = "SELECT row_format AS row_format FROM information_schema.tables WHERE table_schema = \"" + db.strip() + "\" AND table_name = \"" + table.strip() + "\""
        result = self.execute(query)['query_result']
        return result[0]['row_format']

    def get_column_names(self, db, table):
        query = "SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema = '" + db.strip() + "' AND table_name = '" + table.strip() + "' ORDER BY ordinal_position"
        result = self.execute(query)['query_result']
        return result

    def get_pk_columns(self, db, table):
        query = "SELECT COLUMN_NAME FROM information_schema.statistics WHERE table_schema = '" + db.strip() + "' AND table_name = '" + table.strip() + "' AND index_name = 'PRIMARY'"
        result = self.execute(query)['query_result']
        return result
