import os
import sys
import time
import shutil
import calendar
import requests
import re
import signal
import threading
import json
from collections import OrderedDict
from datetime import timedelta

from imports import imports
from progress import progress
from logs import logs
from amazon_s3 import amazon_s3
from validation import validation
from deployment import deployment

class core:
    def __init__(self, args):
        self._args = args

        # Execution Time
        self._start_time = time.time()

        # Execution Threads
        self._args.execution_threads = 1 if self._args.execution_threads is None else self._args.execution_threads

        # Init Classes
        self._imports = imports(self._args)
        self._progress = progress(self._args, self._imports)
        self._logs = logs(self._args)
        self._amazon_s3 = amazon_s3(self._args, self._imports, self._progress)
        self._validation = validation(self._args, self._imports, self._progress)
        self._deployment = deployment(self._args, self._imports, self._progress)

        # Start Meteor Core
        self.__start()

    #############
    # INIT CORE #
    #############
    def __start(self):
        # Register deployment start datetime
        self._progress.start(os.getpid())

        # Perform the Validation
        self.__validate()

        # Perform the Deploy / Test Execution
        if self._args.deploy or self._args.test:
            try:
                status = self.__deploy() # 0: All queries succeeded | 1: Some queries failed
                self.__post_execution(status=status)
            except (Exception, KeyboardInterrupt) as e:
                self.__post_execution(status=2, error=e)

    ##############
    # VALIDATION #
    ##############
    def __validate(self):
        try:
            self._validation.start()

            if self._args.validate:
                signal.signal(signal.SIGINT,signal.SIG_IGN)
                self.clean()
                self.show_execution_time(only_validate=True)
                self._progress.end(execution_status=1)
                sys.exit()

        except (Exception, KeyboardInterrupt) as e:
            signal.signal(signal.SIGINT,signal.SIG_IGN)
            self.clean()
            self.show_execution_time(only_validate=True)
            if e.__class__ == Exception:
                self._progress.error(e)
            else:
                self._progress.end(execution_status=2)
            sys.exit()

    ##########
    # DEPLOY #
    ##########
    def __deploy(self):
        return self._deployment.start()

    ##################
    # POST EXECUTION #
    ##################
    def __post_execution(self, status, error=None):
        # Supress CTRL+C events
        signal.signal(signal.SIGINT,signal.SIG_IGN)

        try:
            # Display error
            if error.__class__ == Exception:
                print("+==================================================================+")
                print("|  ERRORS                                                          |")
                print("+==================================================================+")
                print(error)

            # Get Logs
            logs = self.__get_logs()
            # Get Summary
            summary = self.__summary(logs)       
            # Compile Logs
            self._logs.compile(logs, summary)
            # Upload Logs to S3
            self._amazon_s3.upload_logs()
            # Clean Environments
            self.clean()
            # Slack Message
            if error is None:
                self.slack(status=0, summary=summary)
            elif error.__class__ == KeyboardInterrupt:
                self.slack(status=1, summary=summary)
            elif error.__class__ == Exception:
                self.slack(status=2, summary=summary, error=str(error).rstrip())
            # Show Execution Time
            self.show_execution_time()
            # Show Logs Location
            self.show_logs_location()
            # Track Execution Status
            if error is None:
                self._progress.end(execution_status=status)
            elif error.__class__ == KeyboardInterrupt:
                self._progress.end(execution_status=2)
            elif error.__class__ == Exception:
                self._progress.error(str(error).rstrip())

        except Exception as e:
            # Store Error in the Progress
            self._progress.error(str(e))
            # Clean Environments
            self.clean()
            # Slack Message
            self.slack(status=2, summary=None, error=str(e))
            # Exit Program
            sys.exit()

    def __summary(self, data):
        print("+==================================================================+")
        print("|  SUMMARY                                                         |")
        print("+==================================================================+")
        
        # Init summary
        summary = {}
        summary['total_queries'] = len(data)

        # Init queries progress
        queries = {}

        # Total Queries
        print("- Total Queries: {}".format(summary['total_queries']))

        # Analyze Test Execution Logs 
        summary['meteor_query_error'] = 0
        summary['meteor_query_success'] = 0
        summary['meteor_query_rollback'] = 0

        for d in data:
            # Count Query Errors
            summary['meteor_query_error'] += 1 if int(d['meteor_status']) == 0 else 0
            # Count Query Success
            summary['meteor_query_success'] += 1 if int(d['meteor_status']) == 1 else 0
            # Count Query Rollback
            summary['meteor_query_rollback'] += 1 if int(d['meteor_status']) == 2 else 0

        # Queries Succeeded
        queries_succeeded_value = 0 if summary['total_queries'] == 0 else round(float(summary['meteor_query_success']) / float(summary['total_queries']) * 100, 2)
        print("- Queries Succeeded: {} (~{}%)".format(summary['meteor_query_success'], float(queries_succeeded_value)))

        # Queries Failed
        queries_failed_value = 0 if summary['total_queries'] == 0 else round(float(summary['meteor_query_error']) / float(summary['total_queries']) * 100, 2)
        print("- Queries Failed: {} (~{}%)".format(summary['meteor_query_error'], float(queries_failed_value)))

        # Queries Rollback
        queries_rollback_value = 0 if summary['total_queries'] == 0 else round(float(summary['meteor_query_rollback']) / float(summary['total_queries']) * 100, 2)
        print("- Queries Rollback: {} (~{}%)".format(summary['meteor_query_rollback'], float(queries_rollback_value)))

        # Track progress
        queries['total'] = summary['total_queries']
        queries['succeeded'] = {'t': summary['meteor_query_success'], 'p': float(queries_succeeded_value)}
        queries['failed'] = {'t': summary['meteor_query_error'], 'p': float(queries_failed_value)}
        queries['rollback'] = {'t': summary['meteor_query_rollback'], 'p': float(queries_rollback_value)}

        # Write Progress
        self._progress.track_queries(value=queries)

        # Return Summary
        return summary

    def __get_logs(self):
        print("+==================================================================+")
        print("|  LOGS                                                            |")
        print("+==================================================================+")

        # Merging Logs
        try:
            execution_logs_path = self._args.execution_path + "/execution/"
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
            with open(self._args.execution_path + '/meteor.js', 'w') as f:
                json.dump({"output": environment_logs}, f, separators=(',', ':'))

            # Compress Execution Logs and Delete Uncompressed Folder
            shutil.make_archive(self._args.execution_path + '/execution', 'gztar', self._args.execution_path + '/execution')
            shutil.rmtree(self._args.execution_path + '/execution')

            # Return All Logs
            return environment_logs

        except Exception as e:
            print("--> Error Merging Logs:\n{}".format(str(e)))
            raise

    def clean(self):
        print("+==================================================================+")
        print("|  CLEAN                                                           |")
        print("+==================================================================+")
        status_msg = "- Cleaning Environment..."
        print(status_msg)
        self._progress.track_tasks(value=status_msg[2:])

        # Delete Uncompressed Deployment Folder
        if os.path.exists(self._args.execution_path):
            if os.path.isdir(self._args.execution_path):
                shutil.rmtree(self._args.execution_path)

    def slack(self, status, summary, error=None):
        # Send Slack Message if it's enabled
        if not self._imports.credentials['slack']['enabled']:
            return

        print("+==================================================================+")
        print("|  SLACK                                                           |")
        print("+==================================================================+")
        status_msg = "- Sending Slack to '#{}'...".format(self._imports.credentials['slack']['channel_name'])
        print(status_msg)
        self._progress.track_tasks(value=status_msg[2:])

        # Get Webhook Data
        webhook_url = self._imports.credentials['slack']['webhook_url']

        # Execution
        execution_text = 'Deployment' if self._args.deploy else 'Test'

        # Status
        status_color = 'good' if status == 0 else 'warning' if status == 1 else 'danger'

        # Logs
        logs_path = "{}.tar.gz".format(self._args.execution_path)
        
        # Current Time
        current_time = calendar.timegm(time.gmtime())

        # Queries
        queries = "```"
        for query in self._imports.query_execution.queries.values():
            queries += re.sub(' +', ' ', query.replace("\t", " ")).strip().replace("\n ", "\n") + '\n'
        queries = queries[:1990] + '...```' if len(queries) > 1990 else queries + '```'

        # Overall Time
        overall_time = str(timedelta(seconds=time.time() - self._start_time))

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
                            "title": "Environment",
                            "value": "```{}```".format(self._args.environment),
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
                            "title": "Logs",
                            "value": "```{}```".format(logs_path),
                            "short": False
                        },
                        {
                            "title": "Execution Time",
                            "value": overall_time,
                            "short": True
                        }
                    ],
                    "color": status_color,
                    "ts": current_time
                }
            ]
        }

        # Add execution_user to the webhook_data
        if self._args.execution_user is not None:
            webhook_data['attachments'][0]['fields'].insert(0, {"title": "User", "value": "```{}```".format(self._args.execution_user), "short": False})

        # Show Error Message
        if error is not None:
            error_data = {
                "title": "Error",
                "value": "```{}```".format(error),
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

    def show_execution_time(self, only_validate=False):
        print("+==================================================================+")
        print("|  EXECUTION TIME                                                  |")
        print("+==================================================================+")
        if not only_validate:
            execution_mode = 'Deployment' if self._args.deploy else 'Test Execution'
            # Validation
            validation_time = str(timedelta(seconds=self._validation.time - self._start_time))
            print("- Validation Time: {}".format(validation_time))

            # Deployment / Test Execution
            deployment_time = str(timedelta(seconds=self._deployment.time - self._validation.time))
            print("- {} Time: {}".format(execution_mode, deployment_time))

            # Post Deployment / Test Execution
            post_time = str(timedelta(seconds=time.time() - self._deployment.time))
            print("- Post {} Time: {}".format(execution_mode, post_time))

        # Overall
        overall_time = str(timedelta(seconds=time.time() - self._start_time))
        print("- Overall Time: {}".format(overall_time))

    def show_logs_location(self):
        print("+==================================================================+")
        print("|  OUTPUT                                                          |")
        print("+==================================================================+")
        logs_path = "{}.tar.gz".format(self._args.execution_path)
        print("- Logs: {}".format(logs_path))