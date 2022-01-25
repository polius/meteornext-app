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
import apps.exports.core

class Exports:
    def __init__(self, sql):
        self._sql = sql
        self._notifications = models.notifications.Notifications(sql)

    def start(self, user, item, server, region, path, amazon_s3):
        # Start Process in another thread
        t = threading.Thread(target=self.__core, args=(user, item, server, region, path,amazon_s3,))
        t.daemon = True
        t.start()

    def __core(self, user, item, server, region, paths, amazon_s3):
        try:
            start_time = time.time()
            core = apps.export.core.Core(region)
            self.__check(core)
            self.__core2(start_time, core, user, item, server, region, paths, amazon_s3)
        except Exception as e:
            query = """
                UPDATE `exports`
                SET
                    `status` = 'FAILED',
                    `error` = %s,
                    `ended` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(str(e), self.__utcnow(), item['id']))
            self.__clean(core, region, item, paths)
            self.__slack(item, start_time, 2, str(e))

    def __check(self, core):
        for command in ['curl --version', 'pv --version', 'mysqldump --version', 'aws --version']:
            p = core.execute(command)
            if len(p['stderr']) > 0:
                raise Exception(p['stderr'])

    def __core2(self, start_time, core, user, item, server, region, paths, amazon_s3):
        # Update export status
        query = """
            UPDATE `exports`
            SET
                `status` = 'IN PROGRESS',
                `started` = %s
            WHERE `id` = %s
        """
        self._sql.execute(query, args=(self.__utcnow(), item['id']))

        # Define new path
        path = paths['remote'] if region['ssh_tunnel'] else paths['local']

        # Start export
        export_status = [None]
        url = [None]
        t = threading.Thread(target=self.__export, args=(core, item, server, path, amazon_s3, export_status, url,))
        t.daemon = True
        t.start()

        # Start Monitor
        monitor_status = [None]
        alive = True
        while t.is_alive() and alive:
            alive = self.__monitor(core, item, path, monitor_status)
            time.sleep(1)
        if alive:
            self.__monitor(core, item, path, monitor_status)

        # Generated Presigned URL 
        client = boto3.client('s3', aws_access_key_id=amazon_s3['aws_access_key'], aws_secret_access_key=amazon_s3['aws_secret_access_key'])
        try:
            url[0] = client.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': amazon_s3['bucket'], 'Key': f"exports/{item['uri']}.sql.gz"}, ExpiresIn=86400)
        except Exception as e:
            # Update export status
            query = """
                UPDATE `exports`
                SET
                    `status` = IF(`status` = 'STOPPED', 'STOPPED', 'FAILED'),
                    `ended` = %s,
                    `error` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(self.__utcnow(), str(e), item['id']))
        else:
            # Update export status
            status = 'SUCCESS' if not export_status[0] and not monitor_status[0] else 'FAILED'
            query = """
                UPDATE `exports`
                SET
                    `status` = IF(`status` = 'STOPPED', 'STOPPED', %s),
                    `ended` = %s,
                    `url` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(status, self.__utcnow(), url[0], item['id']))

        # Clean files
        self.__clean(core, region, item, paths)

        # Get export details
        query = """
            SELECT `status`, `error`
            FROM `exports`
            WHERE `id` = %s
        """
        export = self._sql.execute(query, args=(item['id']))[0]

        # Send notification
        if export['status'] in ['SUCCESS','FAILED']:
            notification = {
                'name': f"An export has finished",
                'status': 'ERROR' if export['status'] == 'FAILED' else 'SUCCESS',
                'category': 'utils-export',
                'data': '{{"id":"{}"}}'.format(item['id']),
                'date': self.__utcnow(),
                'show': 1
            }
            self._notifications.post(user_id=user['id'], notification=notification)

        # Send Slack message
        if export['status'] == 'SUCCESS':
            self.__slack(item, start_time, 0)
        elif export['status'] == 'STOPPED':
            self.__slack(item, start_time, 1)
        elif export['status'] == 'FAILED':
            self.__slack(item, start_time, 2, export['error'])

    def __export(self, core, item, server, path, amazon_s3, status, url):
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
            command = f"echo 'EXPORT.{item['uri']}' && export AWS_ACCESS_KEY_ID={amazon_s3['aws_access_key']} && export AWS_SECRET_ACCESS_KEY={amazon_s3['aws_secret_access_key']} && export MYSQL_PWD={server['password']} && mysqldump {options} -h{server['hostname']} -u{server['username']} \"{item['database']}\" {tables} 2> {error_sql_path} | pv -f --size {math.ceil(item['size'] * 1.25)} -F '%p|%b|%r|%t|%e' 2> {progress_path} | gzip -9 | aws s3 cp - s3://{amazon_s3['bucket']}/exports/{item['uri']}.sql.gz 2> {error_aws_path}"

        # Start Import process
        p = core.execute(command)

        # Check if subprocess command has been killed (= stopped by user).
        status[0] = len(p['stderr']) > 0

    def __monitor(self, core, item, path, status):
        # Check if a stop it's been requested
        if not self.__alive(item):
            # SIGKILL
            command = f"ps -U $USER -u $USER u | grep 'EXPORT.{item['uri']}' | grep -v grep | awk '{{print $2}}' | xargs pkill -9 -P 2> /dev/null"
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

        # Update export with progress file
        query = """
            UPDATE `exports`
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
            FROM `exports`
            WHERE `id` = %s
        """
        result = self._sql.execute(query, args=(item['id']))

        if len(result) == 0 or result[0]['stop'] == 1:
            query = """
                UPDATE `exports`
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
                            "value": f"```{item['url']}/utils/export/{item['uri']}```",
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