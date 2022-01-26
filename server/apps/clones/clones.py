import os
import re
import json
import time
import math
import boto3
import shutil
import calendar
import requests
import threading
from datetime import datetime, timedelta

import models.notifications
import apps.clones.core

class Clones:
    def __init__(self, sql):
        self._sql = sql
        self._notifications = models.notifications.Notifications(sql)

    def start(self, user, item, servers, regions, path, amazon_s3):
        # Start Process in another thread
        t = threading.Thread(target=self.__core, args=(user, item, servers, regions, path,amazon_s3,))
        t.daemon = True
        t.start()

    def __core(self, user, item, servers, regions, paths, amazon_s3):
        try:
            start_time = time.time()
            core = {
                "source": apps.clones.core.Core(regions['source']),
                "destination": apps.clones.core.Core(regions['destination'])
            }
            self.__check(core['source'])
            self.__check(core['destination'])
            self.__core2(start_time, core, user, item, servers, regions, paths, amazon_s3)
        except Exception as e:
            query = """
                UPDATE `clones`
                SET
                    `status` = 'FAILED',
                    `error` = %s,
                    `ended` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(str(e), self.__utcnow(), item['id']))
            self.__slack(item, start_time, 2, str(e))
        finally:
            self.__clean(core['source'], regions['source'], item, paths)
            self.__clean(core['destination'], regions['destination'], item, paths)

    def __check(self, core):
        for command in ['curl --version', 'pv --version', 'mysqldump --version', 'aws --version']:
            p = core.execute(command)
            if len(p['stderr']) > 0:
                raise Exception(p['stderr'])

    def __core2(self, start_time, core, user, item, servers, regions, paths, amazon_s3):
        # Update clone status
        query = """
            UPDATE `clones`
            SET
                `status` = 'IN PROGRESS',
                `started` = %s
            WHERE `id` = %s
        """
        self._sql.execute(query, args=(self.__utcnow(), item['id']))

        # Define new path
        path = {
            "source": paths['remote'] if regions['source']['ssh_tunnel'] else paths['local'],
            "destination": paths['remote'] if regions['destination']['ssh_tunnel'] else paths['local']
        }

        # Start Clone (Export)
        export_status = [None]
        url = [None]
        t = threading.Thread(target=self.__export, args=(core['source'], item, servers['source'], path['source'], amazon_s3, export_status,))
        t.daemon = True
        t.start()

        # Start Monitor (Export)
        monitor_status = [None]
        alive = True
        while t.is_alive() and alive:
            alive = self.__monitor_export(core['source'], item, path['source'], monitor_status)
            time.sleep(1)
        if alive:
            self.__monitor_export(core['source'], item, path['source'], monitor_status)

        # Generated Presigned URL 
        client = boto3.client('s3', aws_access_key_id=amazon_s3['aws_access_key'], aws_secret_access_key=amazon_s3['aws_secret_access_key'])
        try:
            url = client.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': amazon_s3['bucket'], 'Key': f"exports/{item['uri']}.sql.gz"}, ExpiresIn=86400)
        except Exception as e:
            # Update export status
            query = """
                UPDATE `clones`
                SET
                    `status` = IF(`status` = 'STOPPED', 'STOPPED', 'FAILED'),
                    `ended` = %s,
                    `error` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(self.__utcnow(), str(e), item['id']))

        # Update clone status
        # status = 'SUCCESS' if not export_status[0] and not monitor_status[0] else 'FAILED'
        # query = """
        #     UPDATE `clones`
        #     SET
        #         `status` = IF(`status` = 'STOPPED', 'STOPPED', %s),
        #         `ended` = %s,
        #         `url` = %s
        #     WHERE `id` = %s
        # """
        # self._sql.execute(query, args=(status, self.__utcnow(), url[0], item['id']))

        # ...

        # Start Clone (Import)
        import_status = [None]
        t = threading.Thread(target=self.__import, args=(core['destination'], item, servers['destination'], path, amazon_s3, import_status,))
        t.daemon = True
        t.start()

        # Start Monitor (Import)
        monitor_status = [None]
        alive = True
        while t.is_alive() and alive:
            alive = self.__monitor_import(core, item, path, monitor_status)
            time.sleep(1)
        if alive:
            self.__monitor_import(core, item, path, monitor_status)

        # Update clone status
        status = 'SUCCESS' if not export_status[0] and not monitor_status[0] else 'FAILED'
        query = """
            UPDATE `clones`
            SET
                `status` = IF(`status` = 'STOPPED', 'STOPPED', %s),
                `ended` = %s,
                `url` = %s
            WHERE `id` = %s
        """
        self._sql.execute(query, args=(status, self.__utcnow(), url[0], item['id']))

        # Get clones details
        query = """
            SELECT `status`, `error`
            FROM `clones`
            WHERE `id` = %s
        """
        clone = self._sql.execute(query, args=(item['id']))[0]

        # Send notification
        if clone['status'] in ['SUCCESS','FAILED']:
            notification = {
                'name': f"A clone has finished",
                'status': 'ERROR' if clone['status'] == 'FAILED' else 'SUCCESS',
                'category': 'utils-clone',
                'data': '{{"id":"{}"}}'.format(item['id']),
                'date': self.__utcnow(),
                'show': 1
            }
            self._notifications.post(user_id=user['id'], notification=notification)

        # Send Slack message
        if clone['status'] == 'SUCCESS':
            self.__slack(item, start_time, 0)
        elif clone['status'] == 'STOPPED':
            self.__slack(item, start_time, 1)
        elif clone['status'] == 'FAILED':
            self.__slack(item, start_time, 2, clone['error'])

    def __export(self, core, item, server, path, amazon_s3, status):
        # Build paths
        error_sql_path = os.path.join(path, item['uri'], 'error_sql.txt')
        error_aws_path = os.path.join(path, item['uri'], 'error_aws.txt')
        progress_path = os.path.join(path, item['uri'], 'progress.txt')

        # Build options
        options = '--single-transaction --max_allowed_packet=1G'
        if not item['export_schema']:
            options += ' --no-create-info'
        elif item['add_drop_table']:
            options += ' --add-drop-table'
        if not item['export_data']:
            options += ' --no-data'
        if item['mode'] == 'partial':
            if not item['export_triggers']:
                options += ' --skip-triggers'
            if item['export_routines']:
                options += ' --routines'
            if item['export_events']:
                options += ' --events'

        # Build tables
        tables = '' if item['mode'] == 'full' else ' '.join(['"' + i['n'].replace('"','\\"') + '"' for i in item['tables']])

        # MySQL & Aurora MySQL engines
        if server['engine'] in ('MySQL', 'Aurora MySQL'):
            command = f"echo 'CLONE.{item['uri']}' && export AWS_ACCESS_KEY_ID={amazon_s3['aws_access_key']} && export AWS_SECRET_ACCESS_KEY={amazon_s3['aws_secret_access_key']} && export MYSQL_PWD={server['password']} && mysqldump {options} -h{server['hostname']} -u{server['username']} \"{item['database']}\" {tables} 2> {error_sql_path} | pv -f --size {math.ceil(item['size'] * 1.25)} -F '%p|%b|%r|%t|%e' 2> {progress_path} | gzip -9 | aws s3 cp - s3://{amazon_s3['bucket']}/clones/{item['uri']}.sql.gz 2> {error_aws_path}"

        # Start Clone process
        p = core.execute(command)

        # Check if subprocess command has been killed (= stopped by user).
        status[0] = len(p['stderr']) > 0

    def __monitor_export(self, core, item, path, status):
        # Check if a stop it's been requested
        if not self.__alive(item):
            # SIGKILL
            command = f"ps -U $USER -u $USER u | grep 'CLONE.{item['uri']}' | grep -v grep | awk '{{print $2}}' | xargs pkill -9 -P 2> /dev/null"
            core.execute(command)
            return False

        # Init path vars
        progress_path = os.path.join(path, item['uri'], 'progress.txt')
        error_sql_path = os.path.join(path, item['uri'], 'error_sql.txt')
        error_aws_path = os.path.join(path, item['uri'], 'error_aws.txt')

        # Read progress file
        p = core.execute(f"[ -f {progress_path} ] && tr '\r' '\n' < '{progress_path}' | sed '/^$/d' | tail -1")
        progress = self.__parse_progress(p['stdout']) if len(p['stdout']) > 0 else None

        # Read error (aws) file
        p = core.execute(f"[ -f {error_aws_path} ] && cat < {error_aws_path}")
        error = self.__parse_error(p['stdout']) if len(p['stdout']) > 0 else None
        if not error:
            # Read error (sql) file
            p = core.execute(f"[ -f {error_sql_path} ] && cat < {error_sql_path}")
            error = self.__parse_error(p['stdout']) if len(p['stdout']) > 0 else None

        # Update status
        status[0] = error

        # Update clone with progress file
        query = """
            UPDATE `clones`
            SET 
                `progress` = %s,
                `error` = %s,
                `updated` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(progress, error, now, item['id']))
        return True

    def __import(self, core, item, server, path, amazon_s3, status):
        # Build paths
        progress_path = os.path.join(path, item['uri'], 'progress.txt')
        error_curl_path = os.path.join(path, item['uri'], 'error_curl.txt')
        error_gunzip_path = os.path.join(path, item['uri'], 'error_gunzip.txt')
        error_sql_path = os.path.join(path, item['uri'], 'error_sql.txt')

        # Get file size
        client = boto3.client('s3', aws_access_key_id=amazon_s3['access_key'], aws_secret_access_key=amazon_s3['secret_key'])
        response = client.head_object(Bucket=amazon_s3['bucket'], Key=f"clones/{item['uri']}.sql.gz")
        size = response['ContentLength']

        # MySQL & Aurora MySQL engines
        if server['engine'] in ('MySQL', 'Aurora MySQL'):
            command = f"echo 'CLONE.{item['uri']}' && export MYSQL_PWD={server['password']} && curl -sSL '{url}' 2> {error_curl_path} | pv -f --size {size} -F '%p|%b|%r|%t|%e' 2> {progress_path} | gunzip 2> {error_gunzip_path} | mysql -h{server['hostname']} -u{server['username']} \"{item['database']}\" 2> {error_sql_path}"

        # Start Import process
        p = core.execute(command)

        # Check if subprocess command has been killed (= stopped by user).
        status[0] = len(p['stderr']) > 0

    def __monitor_import(self, core, item, path, status):
        # Check if a stop it's been requested
        if not self.__alive(item):
            # SIGKILL
            command = f"ps -U $USER -u $USER u | grep 'CLONE.{item['uri']}' | grep -v grep | awk '{{print $2}}' | xargs pkill -9 -P 2> /dev/null"
            core.execute(command)
            core.stop()
            return False

        # Init path vars
        progress_path = os.path.join(path, item['uri'], 'progress.txt')
        error_curl_path = os.path.join(path, item['uri'], 'error_curl.txt')
        error_gunzip_path = os.path.join(path, item['uri'], 'error_gunzip.txt')
        error_sql_path = os.path.join(path, item['uri'], 'error_sql.txt')

        # Read progress file
        p = core.execute(f"[ -f {progress_path} ] && tr '\r' '\n' < '{progress_path}' | sed '/^$/d' | tail -1")
        progress = self.__parse_progress(p['stdout']) if len(p['stdout']) > 0 else None

        # Read error (sql) file
        p = core.execute(f"[ -f {error_sql_path} ] && cat < {error_sql_path}")
        error = self.__parse_error(p['stdout']) if len(p['stdout']) > 0 else None
        if not error:
            # Read error (gunzip) file
            p = core.execute(f"[ -f {error_gunzip_path} ] && cat < {error_gunzip_path}")
            error = self.__parse_error(p['stdout']) if len(p['stdout']) > 0 else None
            if not error:
                # Read error (curl) file
                p = core.execute(f"[ -f {error_curl_path} ] && cat < {error_curl_path}")
                error = self.__parse_error(p['stdout']) if len(p['stdout']) > 0 else None

        # Update status
        status[0] = error

        # Update clone with progress file
        query = """
            UPDATE `clone`
            SET 
                `progress` = %s,
                `error` = %s,
                `updated` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(progress, error, now, item['id']))
        return True

    def __alive(self, item):
        # Check if process has been requested to be stopped
        query = """
            SELECT `stop`
            FROM `clones`
            WHERE `id` = %s
        """
        result = self._sql.execute(query, args=(item['id']))

        if len(result) == 0 or result[0]['stop'] == 1:
            query = """
                UPDATE `clones`
                SET
                    `status` = 'STOPPED',
                    `updated` = %s
                WHERE `id` = %s
            """
            now = self.__utcnow()
            self._sql.execute(query, args=(now, item['id']))
            return False
        return True

    def __clean(self, core, region, item, paths):
        # Remove execution folder from disk (both remote & local)
        if region['ssh_tunnel']:
            core.execute(f"rm -rf {os.path.join(paths['remote'], item['uri'])}")
        shutil.rmtree(os.path.join(paths['local'], item['uri']), ignore_errors=True)

    def __slack(self, item, start_time, status, error=None):
        if not item['slack_enabled']:
            return
        source = f"{item['bucket']}/{item['source']}" if item['mode'] == 'cloud' else item['source']
        webhook_data = {
            "attachments": [
                {
                    "text": "",
                    "fields": [
                        {
                            "title": "User",
                            "value": f"```{item['user']}```",
                            "short": False
                        },
                        {
                            "title": "Mode",
                            "value": f"```{item['mode'].upper()}```",
                            "short": False
                        },
                        {
                            "title": "Source",
                            "value": f"```{source} ({self.__convert_bytes(item['size'])})```",
                            "short": False
                        },
                        {
                            "title": "Server",
                            "value": f"```{item['server_name']} ({item['region_name']})```",
                            "short": False
                        },
                        {
                            "title": "Database",
                            "value": f"```{item['database']}```",
                            "short": False
                        },
                        {
                            "title": "Information",
                            "value": f"```{item['url']}/utils/clones/{item['uri']}```",
                            "short": False
                        },
                        {
                            "title": "Execution Time",
                            "value": str(timedelta(seconds=time.time() - start_time)),
                            "short": True
                        }
                    ],
                    "color": 'good' if status == 0 else 'warning' if status == 1 else 'danger',
                    "ts": calendar.timegm(time.gmtime())
                }
            ]
        }
        if error:
            error_data = {
                "title": "Error",
                "value": f"```{error}```",
                "short": False
            }
            webhook_data["attachments"][0]["fields"].insert(0, error_data)

        # Send the Slack message
        requests.post(item['slack_url'], data=json.dumps(webhook_data), headers={'Content-Type': 'application/json'})

    def __parse_progress(self, string):
        if len(string) == 0:
            return None
        p = re.sub(' +', ' ', string)
        p = p[p.find(']')+1:]
        p = p.replace('\n','').replace('[','').replace(']','').strip()
        p = ' '.join([i.replace(' ', '') for i in p.split('|')]).strip()
        if p.find('%') != -1 and int(p[0:p.find('%')]) > 100:
            p = f"100{p[p.find('%'):]}"
        return p

    def __parse_error(self, string):
        if len(string) == 0:
            return None
        return string.strip()

    def __convert_bytes(self, size):
        for x in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if size < 1024:
                return "%3.2f %s" % (size, x)
            size /= 1024
        return size

    def __utcnow(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
