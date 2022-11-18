import os
import sys
import time
import shutil
import calendar
import requests
import re
import signal
import json
import threading
import sentry_sdk
from collections import OrderedDict
from datetime import timedelta

from firewall import firewall
from imports import imports
from progress import progress
from logs import logs
from amazon_s3 import amazon_s3
from validation import validation
from deployment import deployment
from region import Region
from connector import connector

class core:
    def __init__(self, args):
        self._args = args

        # Execution Time
        self._start_time = time.time()

        # Protect Code Execution
        firewall()

        # Init Classes
        self._imports = imports(self._args)
        self._progress = progress(self._args, self._imports)
        self._logs = logs(self._args, self._imports, self._progress)
        self._amazon_s3 = amazon_s3(self._args, self._imports, self._progress)
        self._validation = validation(self._args, self._imports, self._progress)
        self._deployment = deployment(self._args, self._imports, self._progress)

        # Init sentry
        if self._imports.config['sentry']['enabled']:
            sentry_dsn = 'https://7de474b9a31148d29d10eb5aea1dff71@o1100742.ingest.sentry.io/6138582'
            sentry_sdk.init(dsn=sentry_dsn, environment=self._imports.config['sentry']['environment'], traces_sample_rate=0)

        if self._args.region:
            self.__remote()
        else:
            self.__start()

    ##########
    # REMOTE #
    ##########
    def __remote(self):
        if self._args.compress:
            self._deployment.compress()
        else:
            self._deployment.deploy()

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
                self.__deploy()
                self.__post_execution()
            except (Exception, KeyboardInterrupt) as e:
                self.__post_execution(error=e)

    ##############
    # VALIDATION #
    ##############
    def __validate(self):
        try:
            self._validation.start()

            if self._args.validate:
                signal.signal(signal.SIGINT,signal.SIG_IGN)
                signal.signal(signal.SIGTERM,signal.SIG_IGN)
                self.clean()
                self._progress.end(execution_status=0)
                sys.exit()

        except (Exception, KeyboardInterrupt) as e:
            signal.signal(signal.SIGINT,signal.SIG_IGN)
            signal.signal(signal.SIGTERM,signal.SIG_IGN)
            # Clean regions
            self.clean()
            # Send slack
            if self._args.deploy or self._args.test:
                if e.__class__ == Exception:
                    self.slack(status=2, summary=None, error=str(e))
                elif e.__class__ == KeyboardInterrupt:
                    error = str(e) if len(str(e)) > 0 else None
                    self.slack(status=1, summary=None, error=error)
            # Update progress
            if e.__class__ == Exception:
                self._progress.error(e)
            elif e.__class__ == KeyboardInterrupt:
                error = 1 if len(str(e)) > 0 else 0
                self._progress.end(execution_status=2, error=error)
            # Halt deployment
            sys.exit()

    ##########
    # DEPLOY #
    ##########
    def __deploy(self):
        self._deployment.start()

    ##################
    # POST EXECUTION #
    ##################
    def __post_execution(self, error=None):
        # Supress CTRL+C events
        signal.signal(signal.SIGINT,signal.SIG_IGN)
        signal.signal(signal.SIGTERM,signal.SIG_IGN)

        try:
            # Kill ongoing queries
            if error.__class__ == KeyboardInterrupt:
                self.__kill_queries()
            # Get Logs
            logs = self.__get_logs()
            # Get Summary
            summary = self.__summary(logs)
            # Check Execution Integrity
            error = self.__check_execution(error)
            # Compile Logs
            self._logs.compile(logs, summary, error)
            # Upload Logs to S3
            self._amazon_s3.upload()
            # Clean Environments
            self.clean()
            # Slack Message & Track Execution Status
            if error.__class__ == KeyboardInterrupt:
                self.slack(status=1, summary=summary)
                self._progress.end(execution_status=2)
            elif error.__class__ == Exception:
                self.slack(status=2, summary=summary, error=str(error).rstrip())
                self._progress.error(str(error).rstrip())
            else:
                self.slack(status=0, summary=summary)
                status = 0 if summary['queries_failed'] == 0 else 1
                self._progress.end(execution_status=status)

        except Exception as e:
            # Store Error in the Progress
            self._progress.error(str(e))
            # Clean Environments
            self.clean()
            # Slack Message
            self.slack(status=2, summary=None, error=str(e))
            # Exit Program
            sys.exit()

    def __kill_queries(self):
        threads = []
        for region in self._imports.config['regions']:
            for server in region['sql']:
                connection = {'name': region['name'], 'ssh': region['ssh'], 'sql': server}
                t = threading.Thread(target=self.__kill_queries_server, args=(connection,))
                threads.append(t)
                t.start()
        for t in threads:
            t.join()

    def __kill_queries_server(self, connection):
        conn = connector(connection)
        conn.start()
        try:
            code = '/*' + str(self._imports.config['params']['id']) + '*/'
            results = conn.execute(query=f"SELECT id FROM processlist WHERE info LIKE '{code}%'", database='information_schema')
            if connection['sql']['engine'] == 'MySQL':
                for result in results['query_result']:
                    try:
                        conn.execute(query=f"KILL {result['id']}")
                    except Exception:
                        pass
            elif connection['sql']['engine'] == 'Amazon Aurora (MySQL)':
                for result in results['query_result']:
                    try:
                        conn.execute(query=f"CALL mysql.rds_kill({result['id']})")
                    except Exception:
                        pass
        finally:
            conn.stop()

    def __get_logs(self):
        # Download Logs
        try:
            ssh_regions = [i for i in self._imports.config['regions'] if i['ssh']['enabled']]
            if len(ssh_regions) > 0:
                status_msg = "- Downloading Logs from Regions..."
                self._progress.track_logs(value={'status': 'progress', 'message': status_msg[2:]})
                threads = []
                for region in ssh_regions:
                    r = Region(self._args, region)
                    t = threading.Thread(target=r.get_logs)
                    threads.append(t)
                    t.start()
                for t in threads:
                    t.join()
                self._progress.track_logs(value={'status': 'success'})

        except Exception:
            self._progress.track_logs(value={'status': 'failed'})
            raise

        # If current environment has no regions / servers
        try:
            execution_logs_path = "{}/execution".format(self._args.path)
            region_items = os.listdir(execution_logs_path)
        except FileNotFoundError:
            return []

        # Merge Logs
        try:
            for region_item in region_items:
                if os.path.isdir("{}/{}".format(execution_logs_path, region_item)):
                    region_name = next(item for item in self._imports.config['regions'] if item["id"] == int(region_item))['name']
                    status_msg = f"- Merging {region_name}..."
                    self._progress.track_logs(value={'status': 'progress', 'message': status_msg[2:]})

                    server_items = os.listdir("{}/{}".format(execution_logs_path, region_item))

                    # Merging Server Logs
                    for server_item in server_items:
                        if os.path.isdir("{}/{}/{}".format(execution_logs_path, region_item, server_item)):
                            server_files = os.listdir("{}/{}/{}".format(execution_logs_path, region_item, server_item))
                            server_logs = []
                            for server_file in server_files:
                                # Merging Database Logs
                                with open("{}/{}/{}/{}".format(execution_logs_path, region_item, server_item, server_file)) as database_log:
                                    try:
                                        json_decoded = json.load(database_log, strict=False, object_pairs_hook=OrderedDict)
                                        server_logs.extend(json_decoded['output'])
                                    except Exception:
                                        pass

                            # Write Server File
                            with open("{}/{}/{}.json".format(execution_logs_path, region_item, server_item), 'w') as f:
                                json.dump({"output": server_logs}, f, separators=(',', ':'))

                    # Merging Region Logs
                    region_logs = []
                    server_items = os.listdir("{}/{}".format(execution_logs_path, region_item))
                    for server_item in server_items:
                        if os.path.isfile("{}/{}/{}".format(execution_logs_path, region_item, server_item)) and server_item != 'progress.json':
                            with open("{}/{}/{}".format(execution_logs_path, region_item, server_item)) as server_log:
                                json_decoded = json.load(server_log, strict=False, object_pairs_hook=OrderedDict)
                                region_logs.extend(json_decoded['output'])

                    # Write Region Logs
                    with open("{}/{}.json".format(execution_logs_path, region_item), 'w') as f:
                        json.dump({"output": region_logs}, f, separators=(',', ':'))
                    self._progress.track_logs(value={'status': 'success'})

        except Exception:
            self._progress.track_logs(value={'status': 'failed'})
            raise

        # Merging Environment Logs
        try:
            environment_logs = []
            status_msg = "- Generating a Single Log File..."
            self._progress.track_logs(value={'status': 'progress', 'message': status_msg[2:]})
            region_items = os.listdir(execution_logs_path)
            for region_item in region_items:
                if region_item.endswith('.json'):
                    with open("{}/{}".format(execution_logs_path, region_item)) as f:
                        json_decoded = json.load(f, strict=False, object_pairs_hook=OrderedDict)
                        environment_logs.extend(json_decoded['output'])

        except Exception:
            self._progress.track_logs(value={'status': 'failed'})
            raise

        # Return All Logs
        return environment_logs

    def __summary(self, data):
        # Init summary
        summary = {}
        summary['total_queries'] = len(data)

        # Init queries progress
        queries = {}

        # Analyze Test Execution Logs 
        summary['queries_failed'] = 0
        summary['queries_success'] = 0
        summary['queries_rollback'] = 0

        for d in data:
            # Count Query Errors
            summary['queries_failed'] += 1 if int(d['meteor_status']) == 0 else 0
            # Count Query Success
            summary['queries_success'] += 1 if int(d['meteor_status']) == 1 else 0
            # Count Query Rollback
            summary['queries_rollback'] += 1 if int(d['meteor_status']) == 2 else 0

        # Compute summary
        queries_succeeded_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_success']) / float(summary['total_queries']) * 100, 2)
        queries_failed_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_failed']) / float(summary['total_queries']) * 100, 2)
        queries_rollback_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_rollback']) / float(summary['total_queries']) * 100, 2)

        # Track progress
        queries['total'] = summary['total_queries']
        queries['succeeded'] = {'t': summary['queries_success'], 'p': float(queries_succeeded_value)}
        queries['failed'] = {'t': summary['queries_failed'], 'p': float(queries_failed_value)}
        queries['rollback'] = {'t': summary['queries_rollback'], 'p': float(queries_rollback_value)}

        # Write Progress
        self._progress.track_queries(value=queries)

        # Return Summary
        return summary

    def __check_execution(self, error):
        if error is None:
            result = self._progress.get()
            if 'execution' in result['progress']:
                halted = False
                for i in result['progress']['execution']:
                    halted = any(s['d'] != s['t'] for s in i['servers'])
                    if halted:
                        break
                if halted and result['status'] == 'IN PROGRESS':
                    error = Exception("The execution has been killed by the OS. The deployment has consumed more memory than is available on the region.")
        return error

    def clean(self):
        status_msg = "- Cleaning Regions..."
        self._progress.track_tasks(value={'status': 'progress', 'message': status_msg[2:]})

        # Delete SSH Deployment Logs
        ssh_regions = [i for i in self._imports.config['regions'] if i['ssh']['enabled']]
        threads = []
        if len(ssh_regions) > 0:           
            for region in ssh_regions:
                r = Region(self._args, region)
                t = threading.Thread(target=r.clean)
                t.progress = {}
                threads.append(t)
                t.start()
            for t in threads:
                t.join()

        error = None
        for t in threads:
            if not t.progress['success']:
                error = t.progress
                break
        if error:
            self._progress.track_tasks(value={'status': 'failed'})
        else:
            self._progress.track_tasks(value={'status': 'success'})

        # Delete Deployment Folder
        if os.path.exists(self._args.path):
            if os.path.isdir(self._args.path):
                shutil.rmtree(self._args.path)

    def slack(self, status, summary, error=None):
        # Send Slack Message if it's enabled
        if not self._imports.config['slack']['enabled']:
            return

        status_msg = "- Sending Slack to '#{}'...".format(self._imports.config['slack']['channel_name'])
        self._progress.track_tasks(value={'status': 'progress', 'message': status_msg[2:]})

        # Get Webhook Data
        webhook_url = self._imports.config['slack']['webhook_url']

        # Execution
        execution_text = 'DEPLOY' if self._args.deploy else 'TEST'

        # Status
        status_color = 'good' if status == 0 else 'warning' if status == 1 else 'danger'

        # Logs
        logs_information = f"{self._imports.config['params']['url']}/deployments/{self._args.uri}"
        logs_results = f"{self._imports.config['params']['url']}/results/{self._args.uri}"

        # Current Time
        current_time = calendar.timegm(time.gmtime())

        # Queries
        queries = []
        def parse(data, queries):
            if type(data) is dict:
                for i in data.values():
                    parse(i, queries)
            elif type(data) in [list,set,tuple]:
                for i in data:
                    parse(i, queries)
            else:
                query = re.sub(' +', ' ', str(data).replace("\t", " ")).strip().replace("\n ", "\n")
                if query not in queries:
                    queries.append(query)
        try:
            data = self._imports.blueprint.queries
        except AttributeError:
            pass
        else:
            parse(data, queries)

        parsed_queries = '```' + '\n---\n'.join([i for i in queries])
        parsed_queries = parsed_queries[:1500] + '...```' if len(parsed_queries) > 1500 else parsed_queries + '```'
        parsed_queries = '```---```' if parsed_queries == '``````' else parsed_queries

        # Overall Time
        overall_time = str(timedelta(seconds=time.time() - self._start_time))

        if summary is not None:
            summary_msg = "- Total Queries: {}".format(summary['total_queries'])
            queries_succeeded_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_success']) / float(summary['total_queries']) * 100, 2)
            summary_msg += "\n- Queries Succeeded: {0} (~{1}%)".format(summary['queries_success'], float(queries_succeeded_value))
            queries_failed_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_failed']) / float(summary['total_queries']) * 100, 2)
            summary_msg += "\n- Queries Failed: {0} (~{1}%)".format(summary['queries_failed'], float(queries_failed_value))
            queries_rollback_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_rollback']) / float(summary['total_queries']) * 100, 2)
            summary_msg += "\n- Queries Rollback: {0} (~{1}%)".format(summary['queries_rollback'], float(queries_rollback_value))
        else:
            summary_msg = ''

        # Build Webhook Data
        webhook_data = {
            "attachments": [
                {
                    "text": "",
                    "fields": [
                        {
                            "title": "Name",
                            "value": "```{}```".format(self._imports.config['params']['name']),
                            "short": False
                        },
                        {
                            "title": "Release",
                            "value": "```{}```".format(self._imports.config['params']['release']),
                            "short": False
                        },
                        {
                            "title": "Environment",
                            "value": "```{}```".format(self._imports.config['params']['environment']),
                            "short": False
                        },
                        {
                            "title": "Mode",
                            "value": "```{}```".format(execution_text),
                            "short": False
                        },
                        {
                            "title": "Queries",
                            "value": parsed_queries,
                            "short": False
                        },
                        {
                            "title": "Information",
                            "value": "```{}```".format(logs_information),
                            "short": False
                        },
                        {
                            "title": "Results",
                            "value": "```{}```".format(logs_results),
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
        if self._imports.config['params']['user'] is not None:
            webhook_data['attachments'][0]['fields'].insert(0, {"title": "User", "value": "```{}```".format(self._imports.config['params']['user']), "short": False})
        
        # Add summary to the webhook_data
        if summary is not None:
            webhook_data['attachments'][0]['fields'].insert(6, {"title": "Summary", "value": "```{}```".format(summary_msg), "short": False})

        # Show Error Message
        if error is not None:
            error = error[2:] if error.startswith('- ') else error
            error_data = {
                "title": "Error",
                "value": "```{}```".format(error),
                "short": False
            }
            webhook_data["attachments"][0]["fields"].insert(0, error_data)

        # Show the Webhook Response
        try:
            response = requests.post(webhook_url, data=json.dumps(webhook_data), headers={'Content-Type': 'application/json'})
            if response.status_code != 200:
                raise Exception()
            self._progress.track_tasks(value={'status': 'success'})
            
        except Exception:
            self._progress.track_tasks(value={'status': 'failed'})
