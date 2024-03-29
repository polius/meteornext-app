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
from botocore.client import Config

import models.notifications
import apps.clones.core
import connectors.base

class Clones:
    def __init__(self, sql):
        self._sql = sql
        self._notifications = models.notifications.Notifications(sql)

    def start(self, user, item, servers, regions, paths, amazon_s3):
        try:
            start_time = time.time()
            core = {
                "source": apps.clones.core.Core(regions['source']),
                "destination": apps.clones.core.Core(regions['destination'])
            }
            self.__core(start_time, core, user, item, servers, regions, paths, amazon_s3)
        except Exception as e:
            query = """
                UPDATE `clones`
                SET
                    `status` = 'FAILED',
                    `error` = %s,
                    `ended` = %s,
                    `updated` = %s
                WHERE `id` = %s
            """
            now = self.__utcnow()
            self._sql.execute(query, args=(str(e), now, now, item['id']))
            self.__slack(item, start_time, 2, str(e))
        finally:
            self.__clean(core['source'], regions['source'], item, paths)
            self.__clean(core['destination'], regions['destination'], item, paths)

    def __core(self, start_time, core, user, item, servers, regions, paths, amazon_s3):
        # Check if clone is already stopped
        if not self.__alive(item):
            return

        # Update clone status
        query = """
            UPDATE `clones`
            SET
                `status` = 'IN PROGRESS',
                `started` = %s
            WHERE `id` = %s
        """
        self._sql.execute(query, args=(self.__utcnow(), item['id']))

        # Check requirements
        self.__check(core['source'])
        self.__check(core['destination'])

        # Check if a database has to be created
        self.__create_database(item, servers['destination'], regions['destination'])

        # Define new path
        path = {
            "source": paths['remote'] if regions['source']['ssh_tunnel'] else paths['local'],
            "destination": paths['remote'] if regions['destination']['ssh_tunnel'] else paths['local']
        }

        # Make remote import directory
        if regions['source']['ssh_tunnel']:
            core['source'].execute(f"mkdir -p {os.path.join(path['source'], item['uri'])}")

        if regions['destination']['ssh_tunnel']:
            core['destination'].execute(f"mkdir -p {os.path.join(path['destination'], item['uri'])}")

        # Start Clone (Export)
        proceed = True
        t = threading.Thread(target=self.__export, args=(core['source'], item, servers['source'], path['source'], amazon_s3,))
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
        client = boto3.client('s3', endpoint_url=f"https://s3.{amazon_s3['region']}.amazonaws.com", config=Config(signature_version='s3v4'), region_name=amazon_s3['region'], aws_access_key_id=amazon_s3['aws_access_key'], aws_secret_access_key=amazon_s3['aws_secret_access_key'])
        try:
            url = client.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': amazon_s3['bucket'], 'Key': f"clones/{item['uri']}.sql.gz"}, ExpiresIn=3600)
        except Exception as e:
            proceed = False
            # Update clone status
            query = """
                UPDATE `clones`
                SET
                    `status` = IF(`status` = 'STOPPED', 'STOPPED', 'FAILED'),
                    `error` = %s,
                    `ended` = %s,
                    `updated` = %s
                WHERE `id` = %s
            """
            now = self.__utcnow()
            self._sql.execute(query, args=(str(e), now, now, item['id']))

        if proceed:
            now = self.__utcnow()
            # Update clone status
            if monitor_status[0]:
                proceed = False
                query = """
                    UPDATE `clones`
                    SET
                        `status` = IF(`status` = 'STOPPED', 'STOPPED', 'FAILED'),
                        `url` = %s,
                        `ended` = %s,
                        `updated` = %s
                    WHERE `id` = %s
                """
                self._sql.execute(query, args=(url, now, now, item['id']))
            else:
                query = """
                    UPDATE `clones`
                    SET
                        `progress_export` = IF(LOCATE('%%',progress_export), CONCAT('100',SUBSTRING(progress_export,LOCATE('%%',progress_export))), progress_export),
                        `url` = %s,
                        `updated` = %s
                    WHERE `id` = %s
                """
                self._sql.execute(query, args=(url, now, item['id']))

        if proceed:
            # Start Clone (Import)
            import_status = [None]
            t = threading.Thread(target=self.__import, args=(core['destination'], item, servers['destination'], path['destination'], amazon_s3, url, import_status,))
            t.error = None
            t.start()

            # Start Monitor (Import)
            monitor_status = [None]
            alive = True
            while t.is_alive() and alive:
                alive = self.__monitor_import(core['destination'], item, path['destination'], monitor_status)
                time.sleep(1)
            if alive:
                self.__monitor_import(core['destination'], item, path['destination'], monitor_status)

            # Update clone status
            status = 'SUCCESS' if not monitor_status[0] and not t.error else 'FAILED'
            query = """
                UPDATE `clones`
                SET
                    `status` = IF(`status` = 'STOPPED', 'STOPPED', %s),
                    `url` = %s,
                    `error` = IF (`error` IS NOT NULL, `error`, %s),
                    `ended` = %s,
                    `updated` = %s
                WHERE `id` = %s
            """
            now = self.__utcnow()
            self._sql.execute(query, args=(status, url, t.error, now, now, item['id']))

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
                'name': "A clone has finished.",
                'status': 'ERROR' if clone['status'] == 'FAILED' else 'SUCCESS',
                'category': 'utils-clone',
                'data': f'{{"id":"{item["uri"]}"}}',
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
        # Check "aws"
        p = core.execute('aws --version')
        if len(p['stderr']) > 0 or p['stdout'].startswith('aws-cli/1'):
            raise Exception("[CHECK] AWS CLI v2 is not installed in the server's region.")

    def __create_database(self, item, server, region):
        # Build Connector Data
        data = {'ssh': region, 'sql': server}
        data['ssh']['enabled'] = region['ssh_tunnel']
        # Init Connector
        connector = connectors.base.Base(data)
        # Create / Recreate database
        if item['recreate_database']:
            connector.execute(f"DROP DATABASE IF EXISTS `{item['destination_database']}`")
        connector.execute(f"CREATE DATABASE IF NOT EXISTS `{item['destination_database']}`")

    def __export(self, core, item, server, path, amazon_s3):
        current_thread = threading.current_thread()
        try:
            # Build paths
            error_sql_path = os.path.join(path, item['uri'], 'error_sql.txt')
            error_aws_path = os.path.join(path, item['uri'], 'error_aws.txt')
            progress_path = os.path.join(path, item['uri'], 'progress.txt')

            # Check mysqldump version
            p = core.execute('mysqldump --version')
            is_mariadb = True if 'mariadb' in p['stdout'].lower() else False

            # Build options
            options = '--single-transaction --no-tablespaces --max-allowed-packet=1024M --default-character-set=utf8mb4'
            if not is_mariadb:
                options += ' --set-gtid-purged=OFF'
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
            tables = '' if item['mode'] == 'full' else ' '.join(['"' + i['n'].replace('"','\\"') + '"' for i in json.loads(item['tables'])['t']])

            # Remove definers
            remove_definers = "perl -pe 's/^(?!INSERT)(?:(\w+|\/\*[^\*]+\*\/)[ ]*)*((\/\*![[:digit:]]+)?[ ]*DEFINER[ ]*=[ ]*[^ ]*([^*]*\*\/)?)/$1/'"

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

            # MySQL & Amazon Aurora (MySQL) engines
            if server['engine'] in ('MySQL', 'Amazon Aurora (MySQL)'):
                command = f"echo 'CLONE.{item['uri']}' && export AWS_ACCESS_KEY_ID={amazon_s3['aws_access_key']} && export AWS_SECRET_ACCESS_KEY={amazon_s3['aws_secret_access_key']} && export MYSQL_PWD={server['password']} && mysqldump {options} {ssl} -h{server['hostname']} -P {server['port']} -u{server['username']} \"{item['source_database']}\" {tables} 2> {error_sql_path} | {remove_definers} | pv -f --size {math.ceil(item['size'] * 1.25)} -F '%p|%b|%r|%t|%e' 2> {progress_path} | gzip -9 | aws s3 cp - s3://{amazon_s3['bucket']}/clones/{item['uri']}.sql.gz 2> {error_aws_path}"

            # Start Clone process
            p = core.execute(command)
        except Exception as e:
            current_thread.exception = e

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
                `progress_export` = %s,
                `error` = %s,
                `updated` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(progress, error, now, item['id']))
        return True

    def __import(self, core, item, server, path, amazon_s3, url, status):
        current_thread = threading.current_thread()
        try:
            # Build paths
            progress_path = os.path.join(path, item['uri'], 'progress.txt')
            error_curl_path = os.path.join(path, item['uri'], 'error_curl.txt')
            error_gunzip_path = os.path.join(path, item['uri'], 'error_gunzip.txt')
            error_sql_path = os.path.join(path, item['uri'], 'error_sql.txt')

            # Get file size
            client = boto3.client('s3', region_name=amazon_s3['region'], aws_access_key_id=amazon_s3['aws_access_key'], aws_secret_access_key=amazon_s3['aws_secret_access_key'])
            response = client.head_object(Bucket=amazon_s3['bucket'], Key=f"clones/{item['uri']}.sql.gz")
            size = response['ContentLength']

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

            # MySQL & Amazon Aurora (MySQL) engines
            if server['engine'] in ('MySQL', 'Amazon Aurora (MySQL)'):
                command = f"echo 'CLONE.{item['uri']}' && export MYSQL_PWD={server['password']} && curl -sSL '{url}' 2> {error_curl_path} | pv -f --size {size} -F '%p|%b|%r|%t|%e' 2> {progress_path} | gunzip 2> {error_gunzip_path} | mysql {options} {ssl} -h{server['hostname']} -P {server['port']} -u{server['username']} \"{item['destination_database']}\" 2> {error_sql_path}"

            # Start Import process
            p = core.execute(command)

            # Check if subprocess command has been killed (= stopped by user).
            status[0] = len(p['stderr']) > 0
        except Exception as e:
            current_thread.error = e

    def __monitor_import(self, core, item, path, status):
        # Check if a stop it's been requested
        if not self.__alive(item):
            # SIGKILL
            command = f"ps -U $USER -u $USER u | grep 'CLONE.{item['uri']}' | grep -v grep | awk '{{print $2}}' | xargs pkill -9 -P 2> /dev/null"
            core.execute(command)
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
            UPDATE `clones`
            SET
                `progress_import` = %s,
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
                            "title": "Size",
                            "value": f"```{self.__convert_bytes(item['size'])}```",
                            "short": False
                        },
                        {
                            "title": "Source Server",
                            "value": f"```{item['source_server_name']} ({item['source_region_name']})```",
                            "short": False
                        },
                        {
                            "title": "Source Database",
                            "value": f"```{item['source_database']}```",
                            "short": False
                        },
                        {
                            "title": "Destination Server",
                            "value": f"```{item['destination_server_name']} ({item['destination_region_name']})```",
                            "short": False
                        },
                        {
                            "title": "Destination Database",
                            "value": f"```{item['destination_database']}```",
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
