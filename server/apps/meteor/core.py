import os
import sys
import time
import shutil
import calendar
import requests
import gzip
import re
import signal
import json
import threading
import sentry_sdk
from datetime import timedelta

from firewall import firewall
from imports import imports
from progress import progress
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
        self._amazon_s3 = amazon_s3(self._args, self._imports, self._progress)
        self._validation = validation(self._args, self._imports, self._progress)
        self._deployment = deployment(self._args, self._imports, self._progress)

        # Init sentry
        if self._imports.config['sentry']['enabled']:
            sentry_dsn = ''
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
            self.__get_logs()
            # Merge Logs
            summary = self.__merge_logs()
            # Compress Logs
            self.__compress_logs()
            # Check Execution Integrity
            error = self.__check_execution(error)
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
                self._progress.track_logs(value={'status': 'progress', 'message': 'Downloading Logs from Regions...'})
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

    def __merge_logs(self):
        # Get execution logs path
        execution_logs_path = f"{self._args.path}/execution"

        # Init base summary
        summary = {'queries_failed': 0, 'queries_success': 0, 'queries_rollback': 0}

        # Merge Logs
        try:
            first = True
            with open(f"{self._args.path}.json", 'w', encoding='utf-8') as fwrite:
                fwrite.write('[')
                region_items = [i for i in os.listdir(execution_logs_path) if not i.endswith('.tar.gz')]
                for region_item in region_items:
                    region_name = next(item for item in self._imports.config['regions'] if item["id"] == int(region_item))['name']
                    self._progress.track_logs(value={'status': 'progress', 'message': f"Merging {region_name}..."})
                    if os.path.isdir(f"{execution_logs_path}/{region_item}"):
                        server_items = os.listdir(f"{execution_logs_path}/{region_item}")
                        # Merging Server Logs
                        for server_item in server_items:
                            if os.path.isdir(f"{execution_logs_path}/{region_item}/{server_item}"):
                                server_files = [i for i in os.listdir(f"{execution_logs_path}/{region_item}/{server_item}") if not i.endswith('_tx.jsonl')]
                                for server_file in server_files:
                                    # Merging Database Logs
                                    database_file = f"{execution_logs_path}/{region_item}/{server_item}/{server_file}"
                                    with open(database_file, 'r', encoding='utf-8') as fread:
                                        # Get transactions
                                        transactions = {}
                                        if os.path.exists(database_file[:-6] + '_tx.jsonl'):
                                            with open(database_file[:-6] + '_tx.jsonl', 'r', encoding='utf-8') as ftxread:
                                                transactions = {i['id']: i['status'] for i in [json.loads(i) for i in ftxread.read().splitlines()]}
                                        # Compile server logs
                                        for i in fread:
                                            row = json.loads(i.rstrip('\n|\r'))
                                            # Check transactions
                                            if row['meteor_status'].startswith('tx_'):
                                                row['meteor_status'] = '1' if row['meteor_status'] in transactions and int(transactions[row['meteor_status']]) == 1 else '2'
                                            # Compute summary
                                            summary['queries_failed'] += 1 if int(row['meteor_status']) == 0 else 0
                                            summary['queries_success'] += 1 if int(row['meteor_status']) == 1 else 0
                                            summary['queries_rollback'] += 1 if int(row['meteor_status']) == 2 else 0
                                            # Write row to the log
                                            comma = ',' if not first else ''
                                            fwrite.write(comma + json.dumps(row, default=self.__serializer, separators=(',',':')))
                                            first = False
                    self._progress.track_logs(value={'status': 'success'})
                fwrite.write(']')

            # Compute summary
            summary['total_queries'] = summary['queries_failed'] + summary['queries_success'] + summary['queries_rollback']
            queries_succeeded_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_success']) / float(summary['total_queries']) * 100, 2)
            queries_failed_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_failed']) / float(summary['total_queries']) * 100, 2)
            queries_rollback_value = 0 if summary['total_queries'] == 0 else round(float(summary['queries_rollback']) / float(summary['total_queries']) * 100, 2)

            # Track progress
            queries = {}
            queries['total'] = summary['total_queries']
            queries['succeeded'] = {'t': summary['queries_success'], 'p': float(queries_succeeded_value)}
            queries['failed'] = {'t': summary['queries_failed'], 'p': float(queries_failed_value)}
            queries['rollback'] = {'t': summary['queries_rollback'], 'p': float(queries_rollback_value)}

            # Write Progress
            self._progress.track_queries(value=queries)

            # Return summary
            return summary

        except Exception:
            self._progress.track_logs(value={'status': 'failed'})
            raise

    def __serializer(self, obj):
        return obj.__str__()

    def __compress_logs(self):
        try:
            self._progress.track_logs(value={'status': 'progress', 'message': 'Generating a Single Log File...'})
            file_path = f"{self._args.path}.json"
            with open(file_path, 'rb') as f_in:
                with gzip.open(file_path + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            self._progress.track_logs(value={'status': 'success'})
        except Exception:
            self._progress.track_logs(value={'status': 'failed'})
            raise

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
        self._progress.track_tasks(value={'status': 'progress', 'message': 'Cleaning Regions...'})

        # Delete SSH Deployment Logs
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

        # Delete Deployment Folder
        if os.path.exists(self._args.path):
            if os.path.isdir(self._args.path):
                shutil.rmtree(self._args.path)

        # Delete Deployment Logs
        logs_path = f"{self._args.path}.json"
        if os.path.exists(logs_path):
            os.remove(logs_path)
        if self._imports.config['amazon_s3']['enabled'] and os.path.exists(logs_path + '.gz'):
            os.remove(logs_path + '.gz')

        self._progress.track_tasks(value={'status': 'success'})

    def slack(self, status, summary, error=None):
        # Send Slack Message if it's enabled
        if not self._imports.config['slack']['enabled']:
            return

        self._progress.track_tasks(value={'status': 'progress', 'message': f"Sending Slack to #{self._imports.config['slack']['channel_name']}..."})

        # Get Webhook Data
        webhook_url = self._imports.config['slack']['webhook_url']

        # Execution
        execution_text = 'DEPLOY' if self._args.deploy else 'TEST'

        # Status
        status_color = 'good' if status == 0 else 'warning' if status == 1 else 'danger'

        # Logs
        logs_information = f"{self._imports.config['params']['url']}/deployments/{self._args.path.split('/')[-1]}"
        logs_results = f"{self._imports.config['params']['url']}/results/{self._args.path.split('/')[-1]}"

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