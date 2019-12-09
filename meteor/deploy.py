#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
import shutil
import calendar
import requests
import re
import traceback
import signal
import multiprocessing
import json
import imp
from multiprocessing.managers import SyncManager
from collections import OrderedDict
from datetime import timedelta
from colors import colored
from deploy_environments import deploy_environments
from deploy_queries import deploy_queries
from query import query
from mysql import mysql
from logs import logs
from S3 import S3
from progress import progress


class deploy:
    def __init__(self, logger, args):
        self._logger = logger
        self._args = args

        # Execution Path
        self._SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

        # Init the Logs Class
        self._logs = logs(self._logger, self._args)

        # Generate the basic user logs: 'query_execution.py' & 'credentials.json' files
        if self._args.env_id is None:
            self._logs.generate()

        # Import 'query_execution.py' file dynamically
        query_execution_location = "{}/query_execution.py".format(self._args.logs_path)
        self._query_execution = self.__load_query_execution(query_execution_location)

        # Import the 'credentials.json' file dynamically
        credentials_location = '{}/credentials.json'.format(self._args.logs_path)
        self._credentials = self.__load_credentials(credentials_location)

        # Load the 'query_template.json' file dynamically
        query_template_location = '{}/query_template.json'.format(self._SCRIPT_PATH)
        self._query_template = self.__load_query_template(query_template_location)

        # Store the 'Environment Name', 'Environment Data' and the list of SQL Servers that is going to perform the deploy
        self._ENV_NAME = self._args.environment if self._args.environment else ''
        self._ENV_DATA = {}
        self._SERVERS = []

        # Get the Environments
        self._environments = []
        for key in self._credentials['environments'].keys():
            self._environments.append(key)
        self._environments.sort()

        # Execution Time
        self._START_TIME = time.time()
        self._VALIDATION_TIME = None
        self._EXECUTION_TIME = None

        # Meteor Output Logs
        self._meteor_logs_path = None
        self._meteor_logs_url = None

        # Init the Progress Class
        self._progress = progress(self._logger, self._args, self._credentials)

        # Init the S3 Class
        self._s3 = S3(self._logger, self._args, self._credentials, self._progress)

    def __cls(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def __load_query_execution(self, file_path):
        if not os.path.isfile(file_path):
            print(file_path)
            error_msg = "The 'query_execution.py' has not been found in '{}'".format(file_path)
            self._logger.critical(colored(error_msg, 'red', attrs=['reverse', 'bold']))
            self._progress.error(error_msg)
            sys.exit()

        query_execution = imp.load_source('query_execution', file_path)
        return query_execution.query_execution()

    def __load_credentials(self, json_path):
        try:
            if not os.path.isfile(json_path):
                print("The 'credentials.json' file has not been found in '{}'".format(json_path))
                sys.exit()

            with open(json_path) as data_file:
                data = json.load(data_file, object_pairs_hook=OrderedDict)
                return data

        except Exception:
            error_msg = "The 'credentials.json' file has syntax errors. Please check if it's a valid JSON."
            self._logger.critical(colored(error_msg, 'red', attrs=['reverse', 'bold']))
            self._progress.error(error_msg)
            sys.exit()

    def __load_query_template(self, json_path):
        try:
            with open(json_path) as data_file:
                data = json.load(data_file, object_pairs_hook=OrderedDict)
                return data

        except Exception:
            error_msg = "The 'query_template.json' file has syntax errors. Please check if it's a valid JSON."
            self._logger.critical(colored(error_msg, 'red', attrs=['reverse', 'bold']))
            self._progress.error(error_msg)
            sys.exit()

    def init(self):
        if self._args.usage:
            self.__show_usage()
        else:
            # Validate Args
            self.__validate_args()

            # Init Meteor Core
            self.__init_core()

    def check_remote_execution(self):
        if self._args.env_id is not None:
            if self._args.env_check_sql is not None:
                # Check SQL Connection
                self.validate_sql_connection()
            else:
                try:
                    # Get the Environment to perform the Execution
                    environment = self._credentials['environments'][self._args.environment]
                    # Select the valid environment to validate the SQL connections
                    for env in environment:
                        if env['region'] == self._args.env_id:
                            environment = env
                            break

                    if self._args.env_compress:
                        # Compress Execution Logs
                        compressed_file_name = "{}/logs/{}/execution/{}".format(environment['ssh']['deploy_path'], self._args.uuid, environment['region'])
                        compressed_location = "{}/logs/{}/execution/".format(environment['ssh']['deploy_path'], self._args.uuid)
                        if os.path.isdir(compressed_file_name):
                            shutil.make_archive(compressed_file_name, 'gztar', compressed_location)
                    else:
                        # Start the DryRun/Deploy
                        self.start_query_deploy(environment)

                except KeyboardInterrupt:
                    sys.exit(2)

                except Exception as e:
                    self._logger.critical(traceback.format_exc())
                    sys.exit(1)
     
            # Exit the Execution
            sys.exit(0)

    def __show_usage(self):
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored("‖  USAGE                                                           ‖", "magenta", attrs=['bold']))
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored("# python meteor.py --environment \"environment_name\" (--servers \"server1,server2,servern\") [ --validate [ credentials | queries | regions | all ] | --test | --deploy ]", attrs=['bold']))
        print(colored("\nModes:", 'yellow'))
        print(colored("--validate", attrs=['bold']) + ": Starts the Validation Process (Credentials, Queries, Environments).")
        print(colored("--test", attrs=['bold']) + ":     Performs the Test Execution without executing any queries.")
        print(colored("--deploy", attrs=['bold']) + ":   Performs the Deployment executing all queries.")
        print('')
        print(colored("+------------------------------------------------------------------+", 'magenta'))
        print(colored("| SETUP                                                            |", 'magenta'))
        print(colored("+------------------------------------------------------------------+", 'magenta'))
        print("Edit these two files:")
        print("- " + colored("credentials.json", attrs=['bold']) + ":   This file stores all the configuration to be used in the Test Execution / Deployment Process.")
        print("- " + colored("query_execution.py", attrs=['bold']) + ": This file stores all the logic and all the queries to be executed in the Test Execution / Deployment Process.")
        print("")
    
    def __init_core(self):
        # Register deployment start datetime
        self._progress.start(os.getpid())

        # Perform the Validation
        self.__validate()

        # Perform the Deploy / Test Execution
        if self._args.deploy or self._args.test:
            try:
                # Start the Countdown
                self.__start_countdown()
                # Start the Test Execution
                self.__start()
                # Post Test Execution Success
                self.__post_execution(deploy=self._args.deploy, error=False)
            except (Exception, KeyboardInterrupt) as e:
                # Post Test Execution Failure
                self.__post_execution(deploy=self._args.deploy, error=True, error_msg=e)

    def __post_execution(self, deploy, error, error_msg=None):
        # Supress CTRL+C events
        signal.signal(signal.SIGINT,signal.SIG_IGN)

        try:
            log_name = 'deploy' if deploy else 'test'
            if not error:
                # Get Logs
                logs = self.__get_logs()     
                # Analyze Logs
                summary = self.__analyze_log(logs, log_name)       
                # Compile Logs
                self._logs.compile(logs, summary)
                # Compress Logs Folder
                self._logs.compress()
                # Upload Logs to S3
                self._s3.upload_logs()
                # Clean Environments
                self.clean()
                # Slack Message
                self.slack(status=1, summary=summary)
                # Show Execution Time
                self.show_execution_time()
                # Show Logs Location
                self.show_logs_location()
                # Track Execution Status
                self._progress.end(execution_status=1)

            else:
                status_name = '[SUCCESS]_' if error_msg is None else '[FAILED]_'
                if error_msg.__class__ == Exception:
                    if str(error_msg) != '':
                        print(colored("+==================================================================+", 'red', attrs=['bold']))
                        print(colored("‖  ERROR FOUND IN 'query_execution.py'                             ‖", 'red', attrs=['bold']))
                        print(colored("+==================================================================+", 'red', attrs=['bold']))
                        print(colored("Showing Error Traceback ...", attrs=['bold']))
                        print(str(error_msg).rstrip())

                # Get Logs
                logs = self.__get_logs()
                # Analyze Logs
                summary = self.__analyze_log(logs, log_name)
                # Compile Logs
                self._logs.compile(logs, summary, str(error_msg).rstrip())
                # Compress Logs Folder
                self._logs.compress()
                # Upload Logs to S3
                self._s3.upload_logs()
                # Clean Environments
                self.clean()
                # Slack Message
                if error_msg.__class__ == KeyboardInterrupt:
                    self.slack(status=2, summary=summary)
                elif str(error_msg) == '':
                    self.slack(status=3, summary=summary)
                else:
                    message = str(error_msg).rstrip()
                    self.slack(status=4, summary=summary, error_msg=message)
                # Show Execution Time
                self.show_execution_time()
                # Show Logs Location
                self.show_logs_location()
                # Track Execution Status
                if error_msg.__class__ == KeyboardInterrupt:
                    self._progress.end(execution_status=2)
                elif str(error_msg) != '':
                    self._progress.error(str(error_msg).rstrip())
                else:
                    self._progress.end(execution_status=0)

        except Exception as e:
            print(str(e))
            # Store Error in the Progress
            self._progress.error(str(e))
            # Clean Environments
            self.clean()
            # Slack Message
            self.slack(status=4, summary=None, error_msg=str(e))
            # Exit Program
            sys.exit()

        # Enable CTRL+C events
        signal.signal(signal.SIGINT, signal.default_int_handler)

    def __validate(self):
        ## VALIDATION
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored("‖  VALIDATION                                                      ‖", "magenta", attrs=['bold']))
        print(colored("+==================================================================+", "magenta", attrs=['bold']))

        try:
            validate_regions = False 
            if self._args.validate == 'credentials':
                self.__validate_credentials()

            elif self._args.validate == 'queries':
                self.__validate_queries()

            elif self._args.validate == 'regions':
                validate_regions = True
                self.__validate_regions()

            else:
                self.__validate_credentials()
                self.__validate_queries()
                validate_regions = True
                self.__validate_regions()

            # Store Validation Time
            self._VALIDATION_TIME = time.time()

        except (Exception, KeyboardInterrupt) as e:
            signal.signal(signal.SIGINT,signal.SIG_IGN)
            if e.__class__ == KeyboardInterrupt and not validate_regions:
                print(colored("\n--> Ctrl+C received. Stopping the execution...", 'yellow', attrs=['reverse', 'bold']))
            self._logs.compress()
            self.clean()
            self.show_execution_time(only_validate=True)
            self._progress.end(execution_status=2)
            sys.exit()
        else:
            if self._args.validate:
                signal.signal(signal.SIGINT,signal.SIG_IGN)
                self.clean(remote=(self._args.validate == 'regions' or self._args.validate == 'all'))
                self.show_execution_time(only_validate=True)
                self._progress.end(execution_status=1)

    def __validate_args(self):
        if not self._args.environment:
            raise Exception("[USER] The --environment flag is required")
        if self._args.validate and not self._args.environment:
            raise Exception("[USER] The --validate argument requires the --environment")
        if self._args.test and not self._args.environment:
            raise Exception("[USER] The --test argument requires the --environment")
        if self._args.deploy and not self._args.environment:
            raise Exception("[USER] The --deploy argument requires the --environment")
        
        nargs = 0 
        nargs += 1 if self._args.validate else 0
        nargs += 1 if self._args.test else 0
        nargs += 1 if self._args.deploy else 0

        if nargs > 1 or (not self._args.environment and nargs > 0) or (self._args.environment and nargs == 0):
            raise Exception("[USER] The --environment argument requires [ --validate | --test | --deploy ]")

        if self._args.validate and self._args.validate not in ['all', 'credentials', 'queries', 'regions']:
            raise Exception("[USER] The --validate argument requires [ credentials | queries | regions | all ]")

    def __validate_credentials(self):
        print(colored("+------------------------------------------------------------------+", 'magenta'))
        print(colored("| Validating Credentials                                           |", 'magenta'))
        print(colored("+------------------------------------------------------------------+", 'magenta'))
        try:
            # Check --environment exists
            if self._args.environment not in self._environments:
                raise Exception("The Environment '{}' does not exist.".format(self._args.environment))

            else:
                # Init Global Variables
                self._ENV_DATA[self._args.environment] = self._credentials['environments'][self._args.environment]
                self._ENV_NAME = self._args.environment

                # Get The list of Servers to Perform the Test Execution / Deployment
                for region in self._ENV_DATA[self._args.environment]:
                    for sql in region['sql']:
                        if region['ssh']['enabled'] == 'True':
                            self._SERVERS.append("{0} ({1}) [SSH {2}]".format(sql['name'], sql['hostname'], region['ssh']['hostname']))
                        else:
                            self._SERVERS.append("{0} ({1})".format(sql['name'], sql['hostname']))

            for environment in self._environments:
                regions = self._credentials['environments'][environment]
                regions_list = []
                # Store All SQL IDs
                servers_list = []
                for region in regions:
                    # Region
                    if region['region'] == '':
                        raise Exception("[Environment: {}] The Region can not be empty.".format(environment))
                    elif region['region'] in regions_list:
                        raise Exception("[Environment: {0}] The Region should be unique. There are two regions named '{1}'.".format(environment, region['region']))
                    regions_list.append(region['region'])

                    # SSH
                    if region['ssh']['enabled'] != 'True' and region['ssh']['enabled'] != 'False':
                        raise Exception("[Environment: {}] The SSH enabled should be True or False.".format(environment))
                    if region['ssh']['enabled'] == 'True' and region['ssh']['hostname'] == '':
                        raise Exception("[Environment: {}] The SSH hostname can not be empty.".format(environment))
                    if region['ssh']['enabled'] == 'True' and region['ssh']['deploy_path'] == '':
                        raise Exception("[Environment: {}] The SSH deploy path can not be empty.".format(environment))
                    if region['ssh']['enabled'] == 'True' and region['ssh']['key'] != '' and not os.path.isfile(region['ssh']['key']):
                        raise Exception("[Environment: {}] The SSH key '{}' does not exist in the path provided.".format(environment, region['ssh']['key']))
                    if region['ssh']['enabled'] == 'True' and region['ssh']['deploy_path'].endswith('/'):
                        region['ssh']['deploy_path'] = region['ssh']['deploy_path'][:-1]

                    # SQL
                    for sql in region['sql']:
                        if sql['name'] == '':
                            raise Exception("[Environment: {}] The SQL name should be filled.".format(environment))
                        if sql['hostname'] == '':
                            raise Exception("[Environment: {}] The SQL hostname should be filled.".format(environment))
                        if sql['username'] == '':
                            raise Exception("[Environment: {}] The SQL username should be filled.".format(environment))

                        # Add sql['name'] to the list
                        servers_list.append(sql['name'])
                
                # Check if there are duplicated sql ids in all environment servers
                seen = set()
                seen_add = seen.add
                seen_twice = set( x for x in servers_list if x in seen or seen_add(x) )
                if len(seen_twice) > 0:
                    raise Exception("[Environment: {0}] The server name should be unique. There are two IDs named '{1}'".format(environment, str(list(seen_twice)[0])))

                # Check if the list of --servers exist in the credentials
                if self._args.servers is not None and self._args.environment == environment:
                    servers = self._args.servers.replace(' ', '').split(',') 
                    for s in servers:
                        if s not in servers_list:
                            raise Exception("[Environment: {0}] The Server '{1}' specified with --servers flag does not exist in the environment.".format(environment, s))

            print(colored("- Credentials Validation Passed!", "green", attrs=['bold', 'reverse']))

        except Exception as e:
            print(traceback.format_exc())
            self._progress.error(traceback.format_exc())
            self._logger.critical(colored(e, 'red', attrs=['reverse', 'bold']))
            sys.exit()

    def __validate_queries(self):
        try:
            print(colored("+------------------------------------------------------------------+", 'magenta'))
            print(colored("| Validating Queries                                               |", 'magenta'))
            print(colored("+------------------------------------------------------------------+", 'magenta'))

            validation = query(self._logger, self._args, self._credentials, self._query_template)
            queries_validated = True
            invalid_queries = []

            # Validating Environment Queries
            for q in self._query_execution.queries.values():
                query_parsed = q.replace('\n', '')
                query_parsed = re.sub(' +',' ', query_parsed).strip()
                query_type = validation.get_query_type(q)
                if query_type == False:
                    print(colored('[NOT DETECTED] ', 'red') + query_parsed)
                    queries_validated &= 0
                    invalid_queries.append(query_parsed)
                    self._progress.track_syntax(q)
                else:
                    print(colored('[{}] '.format(query_type.upper()), 'green') + query_parsed)
                    queries_validated &= 1

            # Validating Auxiliary Queries
            for q in self._query_execution.auxiliary_queries.values():
                query_type = validation.get_query_type(q['query'])
                if query_type == False:
                    print(colored('[NOT DETECTED] ', 'red') + colored(q['query']))
                    queries_validated &= 0
                    invalid_queries.append(query_parsed)
                else:
                    print(colored('[{}] '.format(query_type.upper()), 'green') + colored(q['query']))
                    queries_validated &= 1

            # Determine if the queries are validated
            if not queries_validated:
                self._progress.error("Queries not valid")
                raise Exception(colored("- Validation Not Passed. Please review the above queries in the 'query_execution.py' file.", "red"))
            else:
                print(colored("- Queries Validation Passed!", 'green', attrs=['bold', 'reverse']))

        except Exception as e:
            self._logger.critical(colored(e, 'red', attrs=['reverse', 'bold']))
            raise

    def __validate_regions(self):
        try:
            print(colored("+------------------------------------------------------------------+", 'magenta'))
            print(colored("| Validating Regions                                               |", 'magenta'))
            print(colored("+------------------------------------------------------------------+", 'magenta'))

            # Generate App Version
            deploy_env = deploy_environments(self._logger, self._args, self._credentials)
            deploy_env.generate_app_version()  

            # Start the Validation Process
            for environment in [self._args.environment]:
                # Start Environment Validation in Sequential
                if self._credentials['execution_mode']['parallel'] != 'True':
                    validation_succeeded = True
                    for region in self._credentials['environments'][environment]:
                        deploy_env = deploy_environments(self._logger, self._args, self._credentials, environment, region)
                        validation_succeeded &= deploy_env.validate()
                    if not validation_succeeded:
                        raise Exception()

                # Start Environment Validation in Parallel
                else:
                    manager = SyncManager()
                    manager.start(self.__mgr_init)
                    shared_array = manager.list()

                    processes = []
                    try:
                        validation_process = {}
                        for region in self._credentials['environments'][environment]:
                            validation_process[region['region']] = {}
                        self._progress.track_validation(region=validation_process)

                        for region in self._credentials['environments'][environment]:    
                            environment_type = '[LOCAL]' if region['ssh']['enabled'] == 'False' else '[SSH]  '
                            deploy_env = deploy_environments(self._logger, self._args, self._credentials, environment, region)
                            p = multiprocessing.Process(target=deploy_env.validate, args=(False, shared_array,))
                            p.start()
                            processes.append(p)

                        # Track Progress
                        tracking = True
                        while tracking:
                            # Check if all processes have finished
                            if all(not p.is_alive() for p in processes):
                                tracking = False

                            # Get Overall Environment Validation Status
                            for data in shared_array:
                                # Track progress
                                progress = {'success': data['success']}
                                if len(data['progress']) > 0:
                                    progress['errors'] = data['progress']
                                if 'error' in data:
                                    progress['error'] = data['error']
                                self._progress.track_validation(region=data['region'], value=progress)
                                # Check if there are any validation errors
                                if data['success'] is False:
                                    raise Exception()

                            time.sleep(1)

                        # Ensure all processes have finished before proceeding forward
                        for process in processes:
                            process.join()

                    except KeyboardInterrupt:
                        signal.signal(signal.SIGINT,signal.SIG_IGN)
                        print(colored("\n--> Ctrl+C received. Stopping the execution...", 'yellow', attrs=['reverse', 'bold']))
                        for process in processes:
                            process.join()
                        raise

            print(colored("- Regions Validation Passed!", 'green', attrs=['bold', 'reverse']))

        except Exception as e:
            if len(str(e)) > 0:
                self._logger.critical(str(e))
            error_msg = "- Regions Not Passed the Environment Validation."
            self._logger.critical(colored(error_msg, 'red', attrs=['reverse', 'bold']))
            self._progress.error(error_msg[2:])
            self.clean()
            sys.exit()
        
    def validate_sql_connection(self):
        environment = self._credentials['environments'][self._args.environment]
        # Select the valid environment to validate the SQL connections
        for env in environment:
            if env['region'] == self._args.env_id:
                environment = env
                break

        for sql in environment['sql']:
            if sql['name'] == self._args.env_check_sql:
                try:
                    mysql_conn = mysql(self._logger, self._args, self._credentials)
                    mysql_conn.connect(sql['hostname'], sql['username'], sql['password'])
                except Exception as e:
                    print(str(e))
                break
    
    def __start_countdown(self):
        try:
            # Countdown
            countdown_seconds = 1
            countdown_msg = '--> Starting Test Execution in:' if self._args.test else '--> Starting Deployment in:'
            countdown_color = '\033[0;31m'
            self.__countdown(countdown_seconds, countdown_msg, countdown_color)
        except KeyboardInterrupt:
            print("")
            raise

    def __show_execution_header(self, started_datetime, started_time):
        # Show Header
        self.__cls()
        title = "‖  TEST EXECUTION                                                  ‖" if self._args.test else "‖  DEPLOYMENT                                                      ‖"
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored(title, "magenta", attrs=['bold']))
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        # Show Execution Status
        if self._credentials['execution_mode']['parallel'] == 'True':
            elapsed = str(timedelta(seconds=time.time() - started_time))
            print(colored("> Started: ", 'magenta') + colored(started_datetime, attrs=['bold']) + colored(" > Elapsed: ", 'magenta') + colored(elapsed, attrs=['bold']))

    def __start(self, environment_data=None):
        try:
            # Get Deployment Start Datetime
            started_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            started_time = time.time()

            # Show Header
            self.__show_execution_header(started_datetime, started_time)

            # Set Args Variable to Define DryRun/Deploy
            self._args.env_start_deploy = False if self._args.test else True

            # Start Environment Deploy in Sequential
            if self._credentials['execution_mode']['parallel'] != 'True':
                try:
                    for env_data in self._ENV_DATA[self._ENV_NAME]:
                        env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                        env.start()
                except KeyboardInterrupt:
                    print(colored("\n--> Ctrl+C received. Stopping the execution...", 'yellow', attrs=['reverse', 'bold']))
                    raise

            # Start Environment Deploy in Parallel
            else:
                # Initialize Manager
                manager = SyncManager()
                manager.start(self.__mgr_init)
                shared_array = manager.list()
                progress_array = manager.list()
                processes = []
                execution_status = 1  # 0: QUERY_ERROR | 1: SUCCESS

                # Start Deployment
                try:
                    for env_data in self._ENV_DATA[self._ENV_NAME]:
                        env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                        p = multiprocessing.Process(target=env.start, args=(shared_array, progress_array,))
                        p.start()
                        processes.append(p)

                    # Init Progress
                    progress = {}
                    for env_data in self._ENV_DATA[self._ENV_NAME]:
                        progress[env_data['region']] = {}
                        
                    # Track Progress
                    tracking = True
                    while tracking:
                        track_progress = True
                        # Check if all processes have finished
                        if all(not p.is_alive() for p in processes):
                            tracking = False

                        # Check if there are execution errors (e.g. query_execution.py)
                        for data in shared_array:
                            if data['success'] is False:
                                print(colored("- {}Execution Failed.".format('Test ' if self._args.test else ''), 'red', attrs=['bold', 'reverse']))
                                # self._progress.track(key='error', value=data['error'])
                                raise Exception(data['error'])

                        # Calculate Progress
                        for r in range(len(progress_array)):
                            pop = progress_array.pop(0)
                            try:
                                raw_item = pop.decode('utf-8').split('}')
                            except:
                                raw_item = pop.split('}')

                            for i in raw_item:
                                if len(i) > 1:  # Ignore: [u''] & [u'\n']
                                    item = json.loads(''.join(i + '}'))
                                    if 'e' in item:
                                        execution_status = 0
                                        if item['s'] not in progress[item['r']]:
                                            progress[item['r']][item['s']] = { "e": item['e'] }
                                            track_progress = False
                                        else:
                                            progress[item['r']][item['s']]['e'] = item['e']
                                            track_progress = False
                                    else:
                                        if item['s'] not in progress[item['r']] or 'e' not in progress[item['r']][item['s']]:
                                            progress[item['r']][item['s']] = { "p": item['p'], "d": item['d'], "t": item['t'] }
                                        else:
                                            progress[item['r']][item['s']]['p'] = item['p']
                                            progress[item['r']][item['s']]['d'] = item['d']
                                            progress[item['r']][item['s']]['t'] = item['t']

                        # Print & Track Progress
                        self.__show_execution_header(started_datetime, started_time)

                        for r in self._ENV_DATA[self._ENV_NAME]:
                            environment_type = '[LOCAL]' if r['ssh']['enabled'] == 'False' else '[SSH]  '
                            # FIX
                            region_total_databases = sum([int(rp['t']) if 't' in rp else 0 for rp in progress[r['region']].values()])
                            region_databases = sum([int(rp['d']) if 'd' in rp else 0 for rp in progress[r['region']].values()])
                            overall_progress = 0 if region_total_databases == 0 else float(region_databases) / float(region_total_databases) * 100
                            color = 'green' if overall_progress == 100 else 'yellow'
                            print(colored("--> {} Region '{}': {:.2f}% ({}/{} DBs)".format(environment_type, r['region'], overall_progress, region_databases, region_total_databases), color))

                        if track_progress:
                            self._progress.track_execution(value=progress)
                        time.sleep(1)

                    # Ensure all processes have finished before proceeding forward
                    for process in processes:
                        process.join()

                    # Print Execution Status after all executions
                    if execution_status == 0:
                        print(colored("- {}Execution Finished. Some queries failed.".format('Test ' if self._args.test else ''), 'yellow', attrs=['bold', 'reverse']))                        
                        raise Exception('')
                    elif execution_status == 1:
                        print(colored("- {}Execution Finished Successfully.".format('Test ' if self._args.test else ''), "green", attrs=['bold', 'reverse']))

                except KeyboardInterrupt:
                    # Supress CTRL+C events
                    signal.signal(signal.SIGINT,signal.SIG_IGN)
                    print(colored("\n--> Ctrl+C Received. Stopping All Region Processes...", 'yellow', attrs=['reverse', 'bold']))

                    # Send SIGINT to all Region Processes
                    for env_data in self._ENV_DATA[self._ENV_NAME]:
                        env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                        env.sigint()

                    # Check all Remaining Region Processes have finished
                    for env_data in self._ENV_DATA[self._ENV_NAME]:
                        print(colored("- Remaining Processes to Finish in '{}'".format(env_data['region']), attrs=['bold']))
                        env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                        env.check_processes()

                    # Send SIGKILL to clear remaining Zombie Processes
                    print(colored("- Cleaning Remaining Region Processes...", attrs=['bold']))
                    for env_data in self._ENV_DATA[self._ENV_NAME]:
                        env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                        env.sigkill()

                    # Enable CTRL+C events
                    signal.signal(signal.SIGINT, signal.default_int_handler)

                    # Raise KeyboardInterrupt
                    raise
        finally:
            self._EXECUTION_TIME = time.time()        

    #handle SIGINT from SyncManager object
    def mgr_sig_handler(self, signal, frame):
        pass

    #initilizer for SyncManager
    def __mgr_init(self):
        signal.signal(signal.SIGINT, self.mgr_sig_handler)

    def __countdown(self, t, msg, color):
        while t + 1:
            mins, secs = divmod(t, 60)
            timeformat = color + msg + ' {:02d}:{:02d}\033[0m'.format(mins, secs)

            sys.stdout.write("\r" + timeformat)
            sys.stdout.flush()

            time.sleep(1)
            t -= 1
        sys.stdout.write("\n")

    def start_query_deploy(self, env):
        environment_type = '[LOCAL]' if env['ssh']['enabled'] == 'False' else '[SSH]'

        # Create Execution Folders
        if not os.path.exists(self._args.logs_path + '/execution/' + env['region']):
            os.makedirs(self._args.logs_path + '/execution/' + env['region'])

        # Start the Deploy
        deploy = deploy_queries(self._logger, self._args, self._credentials, self._query_template, self._ENV_NAME, env)

        # Execute 'BEFORE' Queries Once per Region
        deploy.execute_before(env['region'])

        # Check if --servers flag is not empty
        servers = self._args.servers.replace(' ', '').split(',') if self._args.servers is not None else None

        # Start Server Deploy in Parallel
        if self._credentials['execution_mode']['parallel'] == 'True':
            manager = SyncManager()
            manager.start(self.__mgr_init)
            shared_array = manager.list()
            alive = True

            processes = []
            try:
                for server in env['sql']:
                    if self._args.servers is None or (self._args.servers is not None and server['name'] in servers):
                        p = multiprocessing.Process(target=deploy.execute_main, args=(env['region'], server, shared_array,))
                        p.start()
                        processes.append(p)

                for process in processes:
                    process.join()

                if len(shared_array) > 0:
                    sys.stderr.write(shared_array[0])
                    sys.stderr.flush() 

            except KeyboardInterrupt:
                for process in processes:
                    process.join()
                raise

        # Start Server Deploy in Sequential
        else:
            for server in env['sql']:
                if self._args.servers is None or (self._args.servers is not None and server['name'] in servers):
                    # Show UI
                    print(colored("+" + "-" * (len(environment_type) + len(self._ENV_NAME) + len(env['region']) + len(server['name']) + len(server['hostname']) + 38) + "+", attrs=['bold']))
                    print(colored("| {0} ENVIRONMENT: {1} - {2} || SQL SERVER: [{3}] {4} |".format(environment_type, self._ENV_NAME, env['region'], server['name'], server['hostname']), attrs=['bold']))
                    print(colored("+" + "-" * (len(environment_type) + len(self._ENV_NAME) + len(env['region']) + len(server['name']) + len(server['hostname']) + 38) + "+", attrs=['bold']))
                    
                    # Start the Query Deploy
                    deploy.execute_main(env['region'], server)

        # Execute 'AFTER' Queries Once per Region
        deploy.execute_after(env['region'])        

    def __analyze_log(self, data, log_name):
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored("‖  SUMMARY                                                         ‖", "magenta", attrs=['bold']))
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        
        # Init summary
        summary = {}
        summary['total_queries'] = len(data)

        # Init queries progress
        queries = {}

        # Total Queries
        print(colored("- Total Queries: ", attrs=['bold']) + colored(summary['total_queries'], 'yellow'))

        # Analyze Test Execution Logs 
        if self._args.test:
            summary['queries_failed'] = 0

            for d in data:
                # Count Executions Test Failed
                summary['queries_failed'] += 1 if int(d['meteor_status']) == 0 else 0

            # Queries Passed the Test Run
            execution_checks_success_value = 0 if summary['total_queries'] == 0 else round(float(summary['total_queries'] - summary['queries_failed']) / float(summary['total_queries']) * 100, 2)        
            print(colored("- Queries Succeeded: ", attrs=['bold']) + colored(summary['total_queries'] - summary['queries_failed'], 'green') + colored(" (~{}%)".format(float(execution_checks_success_value))))

            # Queries Failed the Test Run
            execution_checks_failed_color = 'green' if summary['queries_failed'] == 0 else 'red'
            execution_checks_failed_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_failed']) / float(summary['total_queries']) * 100, 2)        
            print(colored("- Queries Failed: ", attrs=['bold']) + colored(summary['queries_failed'], execution_checks_failed_color) + colored(" (~{}%)".format(float(execution_checks_failed_value))))

            # Track progress
            queries['total'] = summary['total_queries']
            queries['succeeded'] = {'t': summary['total_queries'] - summary['queries_failed'], 'p': float(execution_checks_success_value)}
            queries['failed'] = {'t': summary['queries_failed'], 'p': float(execution_checks_failed_value)}

        # Analyze Deployment Logs 
        elif self._args.deploy:
            summary['meteor_query_error'] = 0

            for d in data:
                # Count Query Errors
                summary['meteor_query_error'] += 1 if int(d['meteor_status']) == 0 else 0

            # Queries Succeeded
            queries_succeeded_value = 0 if summary['total_queries'] == 0 else round(float(int(summary['total_queries']) - int(summary['meteor_query_error'])) / float(summary['total_queries']) * 100, 2)
            print(colored("- Queries Succeeded: ", attrs=['bold']) + colored(int(summary['total_queries']) - int(summary['meteor_query_error']), 'green') + colored(" (~{}%)".format(float(queries_succeeded_value))))

            # Queries Failed
            queries_failed_value = 0 if summary['total_queries'] == 0 else round(float(summary['meteor_query_error']) / float(summary['total_queries']) * 100, 2)
            queries_failed_color = 'green' if summary['meteor_query_error'] == 0 else 'red'
            print(colored("- Queries Failed: ", attrs=['bold']) + colored(summary['meteor_query_error'], queries_failed_color) + colored(" (~{}%)".format(float(queries_failed_value))))

            # Track progress
            queries['total'] = summary['total_queries']
            queries['succeeded'] = {'t': summary['total_queries'] - summary['meteor_query_error'], 'p': float(queries_succeeded_value)}
            queries['failed'] = {'t': summary['meteor_query_error'], 'p': float(queries_failed_value)}

        # Write Progress
        self._progress.track_queries(value=queries)

        # Return Summary
        return summary

    def __get_logs(self):
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored("‖  LOGS                                                            ‖", "magenta", attrs=['bold']))
        print(colored("+==================================================================+", "magenta", attrs=['bold']))

        # 1. Compress Execution Logs
        status_msg = '- Compressing Logs From Remote Hosts...'
        print(status_msg)
        self._progress.track_logs(value=status_msg[2:])

        ## Parallel Mode
        if self._credentials['execution_mode']['parallel'] == 'True':
            manager = SyncManager()
            manager.start(self.__mgr_init)
            shared_array = manager.list()

            processes = []
            try:
                for env_data in self._ENV_DATA[self._ENV_NAME]:
                    if env_data['ssh']['enabled'] == 'True':
                        env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                        p = multiprocessing.Process(target=env.compress_logs, args=(shared_array,))
                        p.start()
                        processes.append(p)

                for process in processes:
                    process.join()

                for data in shared_array:
                    raise Exception(colored("--> Error Compressing Logs:\n{}".format(''.join(data)), 'red'))

            except KeyboardInterrupt:
                for process in processes:
                    process.join()
                raise

        ## Sequential Mode
        else:
            for env_data in self._ENV_DATA[self._ENV_NAME]:
                if env_data['ssh']['enabled'] == 'True':
                    env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                    env.compress_logs()

        # 2. Get SSH Execution Logs
        status_msg = "- Downloading Logs From Remote Hosts..."
        print(status_msg)
        self._progress.track_logs(value=status_msg[2:])

        ## Parallel Mode
        if self._credentials['execution_mode']['parallel'] == 'True':
            manager = SyncManager()
            manager.start(self.__mgr_init)
            shared_array = manager.list()

            processes = []
            for env_data in self._ENV_DATA[self._ENV_NAME]:
                env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                p = multiprocessing.Process(target=env.get_logs, args=(shared_array,))
                p.start()
                processes.append(p)

            for process in processes:
                process.join()

            for data in shared_array:
                raise Exception(colored("--> Error Downloading Logs:\n{}".format(''.join(data)), 'red'))

        ## Sequential Mode
        else:
            for env_data in self._ENV_DATA[self._ENV_NAME]:
                env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                env.get_logs()

        # 3. Merging Logs
        try:
            execution_logs_path = self._args.logs_path + "/execution/"
            region_items = os.listdir(execution_logs_path)

            for region_item in region_items:
                if os.path.isdir(execution_logs_path + region_item):
                    status_msg = "- Merging '{}'...".format(region_item)
                    print(status_msg)
                    self._progress.track_logs(value=status_msg[2:])

                    server_items = os.listdir(execution_logs_path + region_item)

                    # Merging Server Logs
                    for server_item in server_items:
                        if os.path.isdir(execution_logs_path + region_item + '/' + server_item):
                            # print("-- Merging '{}'...".format(server_item))
                            server_files = os.listdir(execution_logs_path + region_item + '/' + server_item)
                            server_logs = []
                            for server_file in server_files:
                                # Merging Database Logs
                                with open(execution_logs_path + region_item + '/' + server_item + '/' + server_file) as database_log:
                                    json_decoded = json.load(database_log, strict=False, object_pairs_hook=OrderedDict)
                                    server_logs.extend(json_decoded['output'])

                            # Write Server File
                            with open(execution_logs_path + region_item + '/' + server_item + '.json', 'w') as f:
                                json.dump({"output": server_logs}, f, separators=(',', ':'))

                    # Merging Region Logs
                    region_logs = []
                    server_items = os.listdir(execution_logs_path + region_item)
                    for server_item in server_items:
                        if os.path.isfile(execution_logs_path + region_item + '/' + server_item):
                            with open(execution_logs_path + region_item + '/' + server_item) as server_log:
                                json_decoded = json.load(server_log, strict=False, object_pairs_hook=OrderedDict)
                                region_logs.extend(json_decoded['output'])

                    # Write Region Logs
                    with open(execution_logs_path + region_item + '.json', 'w') as f:
                        json.dump({"output": region_logs}, f, separators=(',', ':'))

            # Merging Environment Logs
            environment_logs = []
            status_msg = "- Generating a Single Log File..."
            print(status_msg)
            self._progress.track_logs(value=status_msg[2:])

            region_items = os.listdir(execution_logs_path)
            for region_item in region_items:
                if os.path.isfile(execution_logs_path + region_item):
                    with open(execution_logs_path + region_item) as f:
                        json_decoded = json.load(f, strict=False, object_pairs_hook=OrderedDict)
                        environment_logs.extend(json_decoded['output'])

            # Write Environment Log
            with open(self._args.logs_path + '/meteor.js', 'w') as f:
                json.dump({"output": environment_logs}, f, separators=(',', ':'))

            # Compress Execution Logs and Delete Uncompressed Folder
            shutil.make_archive(self._args.logs_path + '/execution', 'gztar', self._args.logs_path + '/execution')
            shutil.rmtree(self._args.logs_path + '/execution')

            # Return All Logs
            return environment_logs

        except Exception:
            raise Exception(colored("--> Error Merging Logs:\n{}".format(traceback.format_exc()), 'red'))

    def clean(self, remote=True):
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored("‖  CLEAN UP                                                        ‖", "magenta", attrs=['bold']))
        print(colored("+==================================================================+", "magenta", attrs=['bold']))

        # Clean Remote Environments
        if remote:
            try:
                status_msg = "- Cleaning Remote Environments..."
                print(status_msg)
                self._progress.track_tasks(value=status_msg[2:])

                if self._ENV_DATA != {}:
                    if self._credentials['execution_mode']['parallel'] == "True":
                        self.__clean_parallel()
                    else:
                        self.__clean_sequential()
                else:
                    for region in self._credentials['environments']:
                        if self._credentials['execution_mode']['parallel'] == "True":
                            self.__clean_parallel(region)
                        else:
                            self.__clean_sequential(region)

            except Exception as e:
                self._logger.error(colored("--> Encountered an error cleaning Remote Environments.\n{}".format(e), 'red'))

        # Send SIGKILL to clear remaining Zombie Processes
        if self._credentials['execution_mode']['parallel'] == 'True' and not self._args.validate:
            status_msg = "- Cleaning Remaining Processes..."
            print(status_msg)
            self._progress.track_tasks(value=status_msg[2:])

            for env_data in self._ENV_DATA[self._ENV_NAME]:
                env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                env.sigkill()

        # Clean Local Environment
        try:
            status_msg = "- Cleaning Local Environment..."
            print(status_msg)
            self._progress.track_tasks(value=status_msg[2:])

            env = deploy_environments(self._logger, self._args, self._credentials)
            env.clean_local()

        except Exception as e:
            self._logger.error(colored("--> Encountered an error cleaning Local Environment.\n{}".format(traceback.format_exc()), 'red'))

    def __clean_sequential(self, region=None):
        env = self._credentials['environments'][region] if region is not None else self._ENV_DATA[self._ENV_NAME]

        for env_data in env:
            if (env_data['ssh']['enabled'] == 'True'):
                env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                env.clean_remote()
    
    def __clean_parallel(self, region=None):
        try:
            manager = SyncManager()
            manager.start(self.__mgr_init)
            shared_array = manager.list()

            processes = []
            env = self._credentials['environments'][region] if region is not None else self._ENV_DATA[self._ENV_NAME]
            for env_data in env:
                if (env_data['ssh']['enabled'] == 'True'):
                    env = deploy_environments(self._logger, self._args, self._credentials, self._ENV_NAME, env_data)
                    p = multiprocessing.Process(target=env.clean_remote, args=(shared_array,))
                    p.start()
                    processes.append(p)

            for process in processes:
                process.join()

            for data in shared_array:
                raise Exception(data)                

        except KeyboardInterrupt:
            for process in processes:
                process.join()
            raise

    def slack(self, status, summary, error_msg=None):
        # Send Slack Message if it's enabled
        if self._credentials['slack']['enabled'] != "True":
            return

        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored("‖  SLACK                                                           ‖", "magenta", attrs=['bold']))
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        status_msg = "- Sending Slack Message to #meteor ..."
        self._logger.info(status_msg)
        self._progress.track_tasks(value=status_msg[2:])

        # Get Webhook Data
        webhook_url = self._credentials['slack']['webhook']

        # Execution
        execution_text = 'Deployment' if self._args.deploy else 'Test'

        # Status
        status_color = 'danger' if status == 4 else 'good' if status in [1,3] else 'warning'
        if self._args.deploy:
            status_text = 'Execution Finished Successfully' if status == 1 else 'Execution Interrupted' if status == 2 else 'Execution Finished with errors' if status == 3 else 'Execution Failed'
        else:
            status_text = 'Test Execution Finished Successfully' if status == 1 else 'Test Execution Interrupted' if status == 2 else 'Test Execution Finished with errors' if status == 3 else 'Test Execution Failed'

        # Logs Path
        logs_path = "{}.tar.gz".format(self._args.logs_path)
        
        # Logs Url
        logs_url = ''
        if self._credentials['web']['public_url'] != '':
            public_url = self._credentials['web']['public_url'] + '/' if not self._credentials['web']['public_url'].endswith('/') else self._credentials['web']['public_url']
            logs_url = "{}?uri={}".format(public_url, self._args.uuid)
        
        # Current Time
        current_time = calendar.timegm(time.gmtime())

        # Servers
        servers = "```"
        for i, s in enumerate(self._SERVERS):
            if i < 5:
                servers += "{}\n".format(s)
        servers = servers[:-1] + '```' if len(self._SERVERS) <= 5 else servers + '...```'

        # Queries
        queries = "```"
        for query in self._query_execution.queries.values():
            queries += re.sub(' +', ' ', query.replace("\t", " ")).strip().replace("\n ", "\n") + '\n'
        queries = queries[:1990] + '...```' if len(queries) > 1990 else queries + '```'

        # Overall Time
        overall_time = str(timedelta(seconds=time.time() - self._START_TIME))

        if summary is not None:
            # Total Queries
            summary_msg = "- Total Queries: {}".format(summary['total_queries'])
            
            if self._args.test:
                summary_msg += "\n+----------------+\n| TEST EXECUTION |\n+----------------+"
                execution_checks_success_value = 0 if summary['total_queries'] == 0 else round(float(summary['total_queries'] - summary['queries_failed']) / float(summary['total_queries']) * 100, 2)
                summary_msg += "\n- Queries Passed the Test Execution: {0} (~{1}%)".format(summary['total_queries'] - summary['queries_failed'], float(execution_checks_success_value))
                execution_checks_failed_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_failed']) / float(summary['total_queries']) * 100, 2)
                summary_msg += "\n- Queries Failed the Test Execution: {0} (~{1}%)".format(summary['queries_failed'], float(execution_checks_failed_value))
            elif self._args.deploy:
                summary_msg += "\n+------------+\n| DEPLOYMENT |\n+------------+"
                queries_succeeded_value = 0 if summary['total_queries'] == 0 else round(float(int(summary['total_queries']) - int(summary['meteor_query_error'])) / float(summary['total_queries']) * 100, 2)
                summary_msg += "\n- Queries Executed Succeeded: {0} (~{1}%)".format(int(summary['total_queries']) - int(summary['meteor_query_error']), float(queries_succeeded_value))
                queries_failed_value = 0 if summary['total_queries'] == 0 else round(float(summary['meteor_query_error']) / float(summary['total_queries']) * 100, 2)
                summary_msg += "\n- Queries Executed Failed: {0} (~{1}%)".format(summary['meteor_query_error'], float(queries_failed_value))
        else:
            summary_msg = ''

        # Build Webhook Data
        webhook_data = {
            "attachments": [
                {
                    "text": "",
                    "fields": [
                        {
                            "title": "Execution",
                            "value": "```{}```".format(execution_text),
                            "short": False
                        },
                        {
                            "title": "Status",
                            "value": "```{}```".format(status_text),
                            "short": False
                        },
                        {
                            "title": "Environment",
                            "value": "```{}```".format(self._ENV_NAME),
                            "short": False
                        },
                        {
                            "title": "Servers",
                            "value": servers,
                            "short": False
                        },
                        {
                            "title": "Queries",
                            "value": queries,
                            "short": False
                        },
                        {
                            "title": "Summary",
                            "value": "```{}```".format(summary_msg),
                            "short": False
                        },
                        {
                            "title": "Logs Path",
                            "value": "```{}```".format(logs_path),
                            "short": False
                        },
                        {
                            "title": "Overall Time",
                            "value": overall_time,
                            "short": True
                        }
                    ],
                    "color": status_color,
                    "ts": current_time
                }
            ]
        }

        # Add Logs URL to the webhook_data
        if logs_url != '':
            logs_url_schema = { 
                "title": "Logs Url",
                "value": "```{}```".format(logs_url),
                "short": False
            }
            webhook_data['attachments'][0]['fields'].insert(len(webhook_data['attachments'][0]['fields'])-1, logs_url_schema)

        # Show Error Message
        if error_msg is not None:
            error_data = {
                "title": "Error",
                "value": "```{}```".format(error_msg),
                "short": False
            }
            webhook_data["attachments"][0]["fields"].insert(1, error_data)

        # Show the Webhook Response
        response = requests.post(webhook_url, data=json.dumps(webhook_data), headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            response = "- Slack Webhook Response: {0} [{1}]".format(str(response.text).upper(), str(response.status_code))
        else:
            response = "- Slack Webhook Response: {0} [{1}]".format(str(response.text).upper(), str(response.status_code))
        
        print(response)
        self._progress.track_tasks(value=response[2:])

    def show_execution_time(self, only_validate=False):
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored("‖  EXECUTION TIME                                                  ‖", "magenta", attrs=['bold']))
        print(colored("+==================================================================+", "magenta", attrs=['bold']))

        if not only_validate:
            if self._EXECUTION_TIME is not None:
                # Validation
                validation_time = str(timedelta(seconds=self._VALIDATION_TIME - self._START_TIME))
                print(colored("- Validation Time: {}".format(validation_time)))

                # Deployment / Test Execution
                deploy_time = str(timedelta(seconds=self._EXECUTION_TIME - self._VALIDATION_TIME))
                if self._args.deploy:
                    print(colored("- Deployment Time: {}".format(deploy_time)))
                elif self._args.test:
                    print(colored("- Test Execution Time: {}".format(deploy_time)))

                # Post Deployment / Test Execution
                post_time = str(timedelta(seconds=time.time() - self._EXECUTION_TIME))
                if self._args.deploy:
                    print(colored("- Post Deployment Time: {}".format(post_time)))
                elif self._args.test:
                    print(colored("- Post Test Execution Time: {}".format(post_time)))

        # Overall
        overall_time = str(timedelta(seconds=time.time() - self._START_TIME))
        print(colored("- Overall Time: {}".format(overall_time), attrs=['bold']))

    def show_logs_location(self):
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        print(colored("‖  OUTPUT                                                          ‖", "magenta", attrs=['bold']))
        print(colored("+==================================================================+", "magenta", attrs=['bold']))
        # Show Logs Path
        self._meteor_logs_path = "{}/{}.tar.gz".format(self._args.logs_path, self._args.uuid)
        print("- Logs Path: " + colored(self._meteor_logs_path, 'green'))

        if self._credentials['web']['public_url'] != '':
            # Show Logs Url
            public_url = self._credentials['web']['public_url'] + '/' if not self._credentials['web']['public_url'].endswith('/') else self._credentials['web']['public_url']
            self._meteor_logs_url = "{}?uri={}".format(public_url, self._args.uuid)
            print("- Logs Url: " + colored(self._meteor_logs_url, 'yellow'))
