#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
import imp
import json
import time
import shutil
import signal
import multiprocessing
from multiprocessing.managers import SyncManager
from query import query
from colors import colored


class deploy_queries:
    def __init__(self, logger, args, credentials, query_template, logs_path, uuid, ENV_NAME=None, ENV_DATA=None):
        self._logger = logger
        self._args = args
        self._credentials = credentials
        self._query_template = query_template
        self._uuid = uuid
        self._environment_name = ENV_NAME
        self._environment_data = ENV_DATA
        self._logs_path = logs_path
        self._script_path = "{}/logs".format(os.path.dirname(os.path.realpath(__file__))) if self._args.logs_path is None else self._args.logs_path

        self._query = query(logger, args, credentials, query_template, ENV_NAME, ENV_DATA)

        if self._environment_data['ssh']['enabled'] == 'True':
            self._query_execution = imp.load_source('query_execution', "{0}/{1}/query_execution.py".format(self._script_path, self._uuid)).query_execution(self._query)
        else:
            self._query_execution = imp.load_source('query_execution', "{}query_execution.py".format(self._logs_path)).query_execution(self._query)

    def execute_before(self, region):
        try:
            # Deploy BEFORE Queries
            if self._credentials['execution_mode']['parallel'] != 'True':
                print(colored("--> Executing BEFORE Queries ...", "yellow", attrs=['bold','reverse']))

            # Start Deploy
            self._query.clear_execution_log()
            self._query_execution.before(self._args.environment, region)

        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

        finally:
            # Supress CTRL+C events
            signal.signal(signal.SIGINT,signal.SIG_IGN)

            # Store Execution Logs
            if self._environment_data['ssh']['enabled'] == 'True':
                execution_log_path = "{0}/{1}/execution/{2}/{2}_before.json".format(self._script_path, self._uuid, self._environment_data['region'])
            else:
                execution_log_path = "{0}execution/{1}/{1}_before.json".format(self._logs_path, self._environment_data['region'])

            with open(execution_log_path, 'w') as outfile:
                json.dump(self._query.execution_log, outfile, default=self.__dtSerializer, separators=(',', ':'))

            # Enable CTRL+C events
            signal.signal(signal.SIGINT, signal.default_int_handler)

    def execute_main(self, region, server, shared_array=None):
        try:
            # Deploy MAIN Queries
            if self._credentials['execution_mode']['parallel'] != 'True':
                print(colored("--> Executing MAIN Queries ...", "yellow", attrs=['bold','reverse']))

            # Set SQL Connection
            self._query.set_sql_connection(server)
            self._query_execution.set_query(self._query)

            # Clear Execution Log
            self._query.clear_execution_log()

            # Get all Databases in current server
            databases = self._query.sql.get_all_databases()

            # Create Execution Server Folder (if exists, then delete+create)
            execution_server_folder = "{0}/{1}/execution/{2}/{3}/".format(self._script_path, self._uuid, region, server['name'])
            if os.path.exists(execution_server_folder):
                shutil.rmtree(execution_server_folder)

            os.mkdir(execution_server_folder)

            # Deployment in Parallel
            if self._credentials['execution_mode']['parallel'] == 'True':
                manager = SyncManager()
                manager.start(self.__mgr_init)
                thread_shared_array = manager.list()
                thread_shared_array.extend(databases)
                progress_array = manager.list()
                processes = []

                try:
                    for i in range(int(self._credentials['execution_mode']['threads'])):
                        p = multiprocessing.Process(target=self.__execute_main_databases, args=(region, server, thread_shared_array, progress_array))
                        p.start()
                        processes.append(p)

                    # Track progress
                    tracking = True
                    while tracking:
                        if all(not p.is_alive() for p in processes):
                            tracking = False
                        d = len(progress_array)
                        progress = float(d)/float(len(databases)) * 100
                        print('{{"r":"{}","s":"{}","p":{:.2f},"d":{},"t":{}}}'.format(region, server['name'], progress, d, len(databases)))
                        if d == len(databases):
                            break
                        time.sleep(1)

                    for process in processes:
                        process.join()

                    if len(thread_shared_array) > 0:
                        shared_array.append(thread_shared_array[0])

                except KeyboardInterrupt:
                    for process in processes:
                        process.join()
                    raise

            # Deploy in Sequential
            else:
                self.__execute_main_databases(region, server, databases)

        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

        except Exception as e:
            if self._credentials['execution_mode']['parallel'] == 'True':
                error_format = re.sub(' +',' ', str(e)).replace('\n', '')
                shared_array.append(error_format)
            raise       

    def __execute_main_databases(self, region, server, thread_shared_array, progress_array=None):
        stdout = sys.stdout
        supress = open('/dev/null', 'w') if progress_array is not None else sys.stdout

        while len(thread_shared_array) > 0:
            # Pick the next database to perform the execution
            try:
                database = thread_shared_array.pop(0)
            except IndexError:
                break

            # Perform the execution to the Database
            try:
                sys.stdout = supress
                self._query_execution.main(self._args.environment, region, server['name'], database)
                sys.stdout = stdout

            except (KeyboardInterrupt, Exception):
                # Supress CTRL+C events
                signal.signal(signal.SIGINT,signal.SIG_IGN)
                sys.stdout = stdout
                # Store Logs
                self.__store_main_logs(region, server, database)
                # Enable CTRL+C events
                signal.signal(signal.SIGINT, signal.default_int_handler)
                # Raise Exception / KeyboardInterrupt
                raise

            # Store Logs the execution to the Database
            try:
                self.__store_main_logs(region, server, database)

            except (KeyboardInterrupt, Exception):
                # Supress CTRL+C events
                signal.signal(signal.SIGINT,signal.SIG_IGN)
                # Store Logs
                self.__store_main_logs(region, server, database)
                # Enable CTRL+C events
                signal.signal(signal.SIGINT, signal.default_int_handler)
                # Raise Exception / KeyboardInterrupt
                raise

            # Add database to the progressed list
            if progress_array is not None:
                progress_array.append(database)

            # Prevent CPU bursting at 100%
            time.sleep(0.001)

    def __store_main_logs(self, region, server, database):
        # Store Logs
        execution_log_path = "{0}/{1}/execution/{2}/{3}/{4}.json".format(self._script_path, self._uuid, self._environment_data['region'], server['name'], database)
        if len(self._query.execution_log['output']) > 0:
            with open(execution_log_path, 'w') as outfile:
                json.dump(self._query.execution_log, outfile, default=self.__dtSerializer, separators=(',', ':'))

        # Check Errors
        for log in self._query.execution_log['output']:
            if (log['meteor_status'] == '0'):
                # Log Query Error in Parallel
                if self._credentials['execution_mode']['parallel'] == 'True':
                    print('{{"r":"{}","s":"{}","e":"{}"}}'.format(region, server['name'], log['meteor_response']))
                break

        # Clear Log
        self._query.clear_execution_log()

    def execute_after(self, region):
        try:
            # Deploy AFTER Queries
            if self._credentials['execution_mode']['parallel'] != 'True':
                print(colored("--> Executing AFTER Queries ...", "yellow", attrs=['bold','reverse']))

            # Start Deploy
            self._query.clear_execution_log()
            self._query_execution.after(self._args.environment, region)

        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

        finally:
            # Supress CTRL+C events
            signal.signal(signal.SIGINT,signal.SIG_IGN)

            # Store Execution Logs
            if self._environment_data['ssh']['enabled'] == 'True':
                execution_log_path = "{0}/{1}/execution/{2}/{2}_after.json".format(self._script_path, self._uuid, self._environment_data['region'])
            else:
                execution_log_path = "{0}execution/{1}/{1}_after.json".format(self._logs_path, self._environment_data['region'])

            with open(execution_log_path, 'w') as outfile:
                json.dump(self._query.execution_log, outfile, default=self.__dtSerializer, separators=(',', ':'))

            # Enable CTRL+C events
            signal.signal(signal.SIGINT, signal.default_int_handler)

    # Parse JSON objects
    def __dtSerializer(self, obj):
        return obj.__str__()

    # Handle SIGINT from SyncManager object
    def __mgr_sig_handler(self, signal, frame):
        pass

    # Initilizer for SyncManager
    def __mgr_init(self):
        signal.signal(signal.SIGINT, self.__mgr_sig_handler)
