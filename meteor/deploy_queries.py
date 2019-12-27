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
import threading
import multiprocessing
from multiprocessing.managers import SyncManager
from query import query
from colors import colored


class deploy_queries:
    def __init__(self, logger, args, credentials, query_template, ENV_NAME=None, ENV_DATA=None):
        self._logger = logger
        self._args = args
        self._credentials = credentials
        self._query_template = query_template
        self._environment_name = ENV_NAME
        self._environment_data = ENV_DATA

        self._query = query(logger, args, credentials, query_template, ENV_NAME, ENV_DATA)
        self._query_execution = imp.load_source('query_execution', "{}/query_execution.py".format(self._args.logs_path)).query_execution(self._query)

        # Store Threading Shared Vars 
        self._databases = []
        self._progress = []

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
            execution_log_path = "{0}/execution/{1}/{1}_before.json".format(self._args.logs_path, self._environment_data['region'])

            with open(execution_log_path, 'w') as outfile:
                json.dump(self._query.execution_log, outfile, default=self.__dtSerializer, separators=(',', ':'))

            # Enable CTRL+C events
            signal.signal(signal.SIGINT, signal.default_int_handler)

    def execute_main(self, region, server):
        try:
            if self._credentials['execution_mode']['parallel'] == 'True':
                thread = threading.current_thread()

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
            self._databases = databases.copy()

            # Create Execution Server Folder (if exists, then delete+create)
            execution_server_folder = "{0}/execution/{1}/{2}/".format(self._args.logs_path, region, server['name'])
            if os.path.exists(execution_server_folder):
                shutil.rmtree(execution_server_folder)

            os.mkdir(execution_server_folder)

            # Deployment in Parallel
            if self._credentials['execution_mode']['parallel'] == 'True':
                try:
                    threads = []
                    for i in range(int(self._credentials['execution_mode']['threads'])):
                        t = threading.Thread(target=self.__execute_main_databases, args=(region, server,))
                        t.alive = True
                        t.start()
                        threads.append(t)

                    # Track progress
                    tracking = True
                    while tracking:
                        if all(not t.is_alive() for t in threads):
                            tracking = False
                        d = len(self._progress)
                        progress = float(d)/float(len(databases)) * 100
                        print('{{"r":"{}","s":"{}","p":{:.2f},"d":{},"t":{}}}'.format(region, server['name'], progress, d, len(databases)))
                        if d == len(self._databases):
                            break
                        time.sleep(1)

                    # Wait all threads
                    self.__wait_threads(threads)

                    if len(self._databases) > 0:
                        thread.progress.append(self._databases[0])

                except KeyboardInterrupt:
                    if self._credentials['execution_mode']['parallel'] == 'True':
                        self.__stop_threads(threads)
                    raise

            # Deploy in Sequential
            else:
                self.__execute_main_databases(region, server)

            # Close SQL Connection
            self._query.close_sql_connection()

        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

        except Exception as e:
            if self._credentials['execution_mode']['parallel'] == 'True':
                error_format = re.sub(' +',' ', str(e)).replace('\n', '')
                thread.progress.append(error_format)
            raise       

    def __execute_main_databases(self, region, server):
        if self._credentials['execution_mode']['parallel'] == 'True':
            t = threading.current_thread()

        # Set SQL Connection
        self._query.set_sql_connection(server)
        self._query_execution.set_query(self._query)

        while len(self._databases) > 0:
            # Detect Thread KeyboardInterrupt
            if self._credentials['execution_mode']['parallel'] == 'True' and not t.alive:
                break

            # Pick the next database to perform the execution
            try:
                database = self._databases.pop(0)
            except IndexError:
                break

            # Perform the execution to the Database
            try:
                self._query_execution.main(self._args.environment, region, server['name'], database)
            except Exception:
                # Supress CTRL+C events
                signal.signal(signal.SIGINT,signal.SIG_IGN)
                # Store Logs
                self.__store_main_logs(region, server, database)
                # Enable CTRL+C events
                signal.signal(signal.SIGINT, signal.default_int_handler)
                # Raise Exception
                raise

            # Store Logs the execution to the Database
            try:
                self.__store_main_logs(region, server, database)
            except Exception:
                # Supress CTRL+C events
                signal.signal(signal.SIGINT,signal.SIG_IGN)
                # Store Logs
                self.__store_main_logs(region, server, database)
                # Enable CTRL+C events
                signal.signal(signal.SIGINT, signal.default_int_handler)
                # Raise Exception / KeyboardInterrupt
                raise

            # Add database to the progressed list
            if self._credentials['execution_mode']['parallel'] == 'True':
                self._progress.append(database)

            # Prevent CPU bursting at 100%
            # time.sleep(0.001)

        # Close SQL Connection
        self._query.close_sql_connection()

    def __store_main_logs(self, region, server, database):
        # Store Logs
        execution_log_path = "{0}/execution/{1}/{2}/{3}.json".format(self._args.logs_path, self._environment_data['region'], server['name'], database)
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
            execution_log_path = "{0}/execution/{1}/{1}_after.json".format(self._args.logs_path, self._environment_data['region'])

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
        
    def __wait_threads(self, threads):
        running = True
        while running:
            running = False
            for t in threads:
                if t.is_alive():
                    t.join(0.1)
                    running = True
        
    def __stop_threads(self, threads):
        for t in threads:
            t.alive = False
        self.__wait_threads(threads)