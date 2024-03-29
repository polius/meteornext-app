import os
import re
import json
import time
import boto3
import shutil
import calendar
import requests
import threading
from datetime import datetime, timedelta
from botocore.client import Config

import models.notifications
import apps.imports.core
import connectors.base

class Imports:
    def __init__(self, sql):
        self._sql = sql
        self._notifications = models.notifications.Notifications(sql)

    def start(self, user, item, server, region, paths, amazon_s3):
        try:
            start_time = time.time()
            core = apps.imports.core.Core(self._sql, item['id'], region)
            self.__core(start_time, core, user, item, server, region, paths, amazon_s3)
        except Exception as e:
            query = """
                UPDATE `imports`
                SET
                    `status` = 'FAILED',
                    `error` = %s,
                    `ended` = %s,
                    `updated` = %s
                WHERE `id` = %s
            """
            now = self.__utcnow()
            self._sql.execute(query, args=(str(e), now, now, item['id']))
            self.__clean(core, region, item, paths)
            self.__slack(item, amazon_s3, start_time, 2, str(e))

    def __core(self, start_time, core, user, item, server, region, paths, amazon_s3):
        # Check if import is already stopped
        if not self.__alive(item):
            return

        # Update import status
        query = """
            UPDATE `imports`
            SET
                `status` = 'IN PROGRESS',
                `started` = %s
            WHERE `id` = %s
        """
        self._sql.execute(query, args=(self.__utcnow(), item['id']))

        # Check requirements
        self.__check(core)

        # Check if a database has to be created
        self.__create_database(item, server, region)

        # Check Cross Region import
        if region['ssh_tunnel']:
            # Make remote import directory
            core.execute(f"mkdir -p {os.path.join(paths['remote'], item['uri'])}")
            if item['mode'] == 'file':
                t = threading.Thread(target=self.__upload, args=(core, item, paths,))
                t.exception = None
                t.start()
                while t.is_alive():
                    if not self.__alive(item):
                        core.stop()
                        self.__clean(core, region, item, paths)
                        self.__slack(item, amazon_s3, start_time, 1)
                        return
                    time.sleep(1)
                if t.exception is not None:
                    raise t.exception

        # Start Import
        t = threading.Thread(target=self.__import, args=(core, item, server, region, paths, amazon_s3))
        t.exception = None
        t.start()

        # Start Monitor
        monitor_status = [None]
        alive = True
        while t.is_alive() and alive:
            alive = self.__monitor(core, item, region, paths, monitor_status)
            time.sleep(1)
        if alive:
            self.__monitor(core, item, region, paths, monitor_status)

        # Update import status
        now = self.__utcnow()
        if t.exception:
            query = """
                UPDATE `imports`
                SET
                    `status` = 'FAILED',
                    `error` = %s,
                    `ended` = %s,
                    `updated` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(str(t.exception), now, now, item['id']))
        else:
            status = 'SUCCESS' if not monitor_status[0] else 'FAILED'
            query = """
                UPDATE `imports`
                SET
                    `status` = IF(`status` = 'STOPPED', 'STOPPED', %s),
                    `ended` = %s,
                    `updated` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(status, now, now, item['id']))

        # Clean files
        self.__clean(core, region, item, paths)

        # Get import details
        query = """
            SELECT `status`, `error`
            FROM `imports`
            WHERE `id` = %s
        """
        imp = self._sql.execute(query, args=(item['id']))[0]

        # Send notification
        if imp['status'] in ['SUCCESS','FAILED']:
            notification = {
                'name': "An import has finished.",
                'status': 'ERROR' if imp['status'] == 'FAILED' else 'SUCCESS',
                'category': 'utils-import',
                'data': f'{{"id":"{item["uri"]}"}}',
                'date': self.__utcnow(),
                'show': 1
            }
            self._notifications.post(user_id=user['id'], notification=notification)

        # Send Slack message
        if imp['status'] == 'SUCCESS':
            self.__slack(item, amazon_s3, start_time, 0)
        elif imp['status'] == 'STOPPED':
            self.__slack(item, amazon_s3, start_time, 1)
        elif imp['status'] == 'FAILED':
            self.__slack(item, amazon_s3, start_time, 2, imp['error'])

    def __check(self, core):
        # Check "curl"
        if len(core.execute('curl --version')['stderr']) > 0:
            raise Exception("[CHECK] curl is not installed in the server's region.")
        # Check "pv"
        if len(core.execute('pv --version')['stderr']) > 0:
            raise Exception("[CHECK] pv is not installed in the server's region.")
        # Check "mysqldump"
        if len(core.execute('mysqldump --version')['stderr']) > 0:
            raise Exception("[CHECK] mysqldump is not installed in the server's region.")

    def __create_database(self, item, server, region):
        # Build Connector Data
        data = {'ssh': region, 'sql': server}
        data['ssh']['enabled'] = region['ssh_tunnel']
        # Init Connector
        connector = connectors.base.Base(data)
        # Create / Recreate database
        if item['recreate_database']:
            connector.execute(f"DROP DATABASE IF EXISTS `{item['database']}`")
        connector.execute(f"CREATE DATABASE IF NOT EXISTS `{item['database']}`")

    def __import(self, core, item, server, region, paths, amazon_s3):
        current_thread = threading.current_thread()
        try:
            # Define path
            path = paths['remote'] if region['ssh_tunnel'] else paths['local']

            # Build paths
            error_curl_path = os.path.join(path, item['uri'], 'error_curl.txt')
            error_gunzip_path = os.path.join(path, item['uri'], 'error_gunzip.txt')
            error_gunzip2_path = os.path.join(path, item['uri'], 'error_gunzip2.txt')
            error_sql_path = os.path.join(path, item['uri'], 'error_sql.txt')
            progress_path = os.path.join(path, item['uri'], 'progress.txt')
            file_path = os.path.join(path, item['uri'], item['source'])

            # Check compressed file
            gunzip = ''
            if item['source'].endswith('.tar') or item['format'] == '.tar':
                gunzip = f"| tar --warning=none -xO {' '.join(item['selected'])} 2> {error_gunzip_path}"
            elif item['source'].endswith('.tar.gz') or item['format'] == '.tar.gz':
                gunzip = f"| tar --warning=none -zxO {' '.join(item['selected'])} 2> {error_gunzip_path}"
            elif item['source'].endswith('.gz') or item['format'] == '.gz':
                gunzip = f"| zcat -q 2> {error_gunzip_path}"
            if item['selected'] and item['selected'][0].endswith('.gz'):
                gunzip += f" | zcat -q 2> {error_gunzip2_path}"

            # Build options
            options = '--max-allowed-packet=1024M --default-character-set=utf8mb4'

            # Check SSL
            ssl = ''
            if server['ssl']:
                ssl += "--ssl-mode=VERIFY_IDENTITY"
                if server['ssl_client_key']:
                    core.execute(f"echo '{server['ssl_client_key']}' > {os.path.join(path, item['uri'], 'ssl_client_key.pem')}")
                    ssl += f" --ssl-key={os.path.join(path, item['uri'], 'ssl_client_key.pem')}"
                if server['ssl_client_certificate']:
                    core.execute(f"echo '{server['ssl_client_certificate']}' > {os.path.join(path, item['uri'], 'ssl_client_certificate.pem')}")
                    ssl += f" --ssl-cert={os.path.join(path, item['uri'], 'ssl_client_certificate.pem')}"
                if server['ssl_ca_certificate']:
                    core.execute(f"echo '{server['ssl_ca_certificate']}' > {os.path.join(path, item['uri'], 'ssl_ca_certificate.pem')}")
                    ssl += f" --ssl-ca={os.path.join(path, item['uri'], 'ssl_ca_certificate.pem')}"

            if item['mode'] == 'cloud':
                client = boto3.client('s3', endpoint_url=f"https://s3.{amazon_s3['region']}.amazonaws.com", config=Config(signature_version='s3v4'), region_name=amazon_s3['region'], aws_access_key_id=amazon_s3['aws_access_key'], aws_secret_access_key=amazon_s3['aws_secret_access_key'])

            # MySQL & Amazon Aurora (MySQL) engines
            if server['engine'] in ('MySQL', 'Amazon Aurora (MySQL)'):
                if item['mode'] == 'file':
                    command = f"echo 'IMPORT.{item['uri']}'; export MYSQL_PWD={server['password']}; pv -f --size {item['size']} -F '%p|%b|%r|%t|%e' {file_path} 2> {progress_path} {gunzip} | mysql {options} {ssl} -h{server['hostname']} -P {server['port']} -u{server['username']} \"{item['database']}\" 2> {error_sql_path}"
                elif item['mode'] in ['url','cloud']:
                    source = client.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': amazon_s3['bucket'], 'Key': item['source']}, ExpiresIn=30) if item['mode'] == 'cloud' else item['source']
                    command = f"echo 'IMPORT.{item['uri']}' && export MYSQL_PWD={server['password']} && curl -sSL '{source}' 2> {error_curl_path} | pv -f --size {item['size']} -F '%p|%b|%r|%t|%e' 2> {progress_path} {gunzip} | mysql {options} {ssl} -h{server['hostname']} -P {server['port']} -u{server['username']} \"{item['database']}\" 2> {error_sql_path}"

            # Start Import process
            core.execute(command)
        except Exception as e:
            current_thread.exception = e

    def __monitor(self, core, item, region, paths, status):
        # Define path
        path = paths['remote'] if region['ssh_tunnel'] else paths['local']

        # Check if a stop it's been requested
        if not self.__alive(item):
            # SIGKILL
            command = f"ps -U $USER -u $USER u | grep 'IMPORT.{item['uri']}' | grep -v grep | awk '{{print $2}}' | xargs pkill -9 -P 2> /dev/null"
            core.execute(command)
            core.stop()
            return False

        # Init path vars
        progress_path = os.path.join(path, item['uri'], 'progress.txt')
        error_curl_path = os.path.join(path, item['uri'], 'error_curl.txt')
        error_gunzip_path = os.path.join(path, item['uri'], 'error_gunzip.txt')
        error_gunzip2_path = os.path.join(path, item['uri'], 'error_gunzip2.txt')
        error_sql_path = os.path.join(path, item['uri'], 'error_sql.txt')

        # Read progress file
        p = core.execute(f"[ -f {progress_path} ] && tr '\r' '\n' < '{progress_path}' | sed '/^$/d' | tail -1")
        progress = self.__parse_progress(p['stdout']) if len(p['stdout']) > 0 else None

        # Read error (sql) file
        p = core.execute(f"[ -f {error_sql_path} ] && cat < {error_sql_path}")
        error = self.__parse_error(p['stdout']) if len(p['stdout']) > 0 else None

        if not error:
            # Read error (gunzip2) file
            p = core.execute(f"[ -f {error_gunzip2_path} ] && cat < {error_gunzip2_path}")
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

        # Update import with progress file
        query = """
            UPDATE `imports`
            SET 
                `progress` = %s,
                `error` = %s,
                `updated` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(progress, error, now, item['id']))
        return True

    def __upload(self, core, item, paths):
        current_thread = threading.current_thread()
        # Upload file
        try:
            core.put(os.path.join(paths['local'], item['uri'], item['source']), os.path.join(paths['remote'], item['uri'], item['source']))
        except Exception as e:
            current_thread.exception = e

    def __alive(self, item):
        # Check if process has been requested to be stopped
        query = """
            SELECT `stop`
            FROM `imports`
            WHERE `id` = %s
        """
        result = self._sql.execute(query, args=(item['id']))

        if len(result) == 0 or result[0]['stop'] == 1:
            query = """
                UPDATE `imports`
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

    def __slack(self, item, amazon_s3, start_time, status, error=None):
        if not item['slack_enabled']:
            return
        source = f"{amazon_s3['bucket']}/{item['source']}" if item['mode'] == 'cloud' else item['source']
        webhook_data = {
            "attachments": [
                {
                    "text": "",
                    "fields": [
                        {
                            "title": "User",
                            "value": f"```{item['username']}```",
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
                            "value": f"```{item['url']}/utils/imports/{item['uri']}```",
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
        return p

    def __parse_error(self, string):
        if len(string) == 0 or string.lower().startswith('warning'):
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
