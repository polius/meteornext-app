import os
import re
import time
import boto3
import shutil
import psutil
import signal
import time
import threading
from datetime import datetime

import models.notifications
import apps.restore.core

class Restore:
    def __init__(self, sql):
        self._sql = sql
        self._notifications = models.notifications.Notifications(sql)

    def start(self, user, item, server, region, path):
        # Start Process in another thread
        t = threading.Thread(target=self.__core, args=(user, item, server, region, path,))
        t.daemon = True
        t.start()

    def __core(self, user, item, server, region, paths):
        try:
            core = apps.restore.core.Core(self._sql, item['id'], region)
            self.__core2(core, user, item, server, region, paths)
        except Exception as e:
            query = """
                UPDATE `restore`
                SET
                    `status` = 'FAILED',
                    `error` = %s,
                    `ended` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(str(e), self.__utcnow(), item['id']))
            self.__clean(core, region, item, paths)

    def __core2(self, core, user, item, server, region, paths):
        # Update restore status
        query = """
            UPDATE `restore`
            SET
                `status` = 'IN PROGRESS',
                `started` = %s
            WHERE `id` = %s
        """
        self._sql.execute(query, args=(self.__utcnow(), item['id']))

        # Check Cross Region restore
        if region['ssh_tunnel']:
            # Make remote restore directory
            core.execute(f"mkdir -p {os.path.join(paths['remote'], item['uri'])}")
            if item['mode'] == 'file':
                t = threading.Thread(target=self.__upload, args=(core, item, paths,))
                t.daemon = True
                t.start()
                while t.is_alive():
                    if not self.__alive(item):
                        core.stop()
                        self.__clean(core, region, item, paths)
                        return
                    time.sleep(1)

        # Define new path
        path = paths['remote'] if region['ssh_tunnel'] else paths['local']

        # Start Import
        import_status = [None]
        t = threading.Thread(target=self.__import, args=(core, item, server, path, import_status,))
        t.start()

        # Start Monitor
        monitor_status = [None]
        alive = True
        while t.is_alive() and alive:
            alive = self.__monitor(core, item, path, monitor_status)
            time.sleep(1)
        if alive:
            self.__monitor(core, item, path, monitor_status)

        # Update restore status
        status = 'SUCCESS' if not import_status[0] and not monitor_status[0] else 'FAILED'
        query = """
            UPDATE `restore`
            SET
                `status` = IF(`status` = 'STOPPED', 'STOPPED', %s),
                `ended` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(status, now, item['id']))

        # Send notification
        if  not import_status[0]:
            notification = {
                'name': f"A restore has finished",
                'status': 'ERROR' if status == 'FAILED' else 'SUCCESS',
                'category': 'utils-restore',
                'data': '{{"id":"{}"}}'.format(item['id']),
                'date': self.__utcnow(),
                'show': 1
            }
            self._notifications.post(user_id=user['id'], notification=notification)

        # Clean files
        self.__clean(core, region, item, paths)

    def __import(self, core, item, server, path, status):
        # Build paths
        error_path = os.path.join(path, item['uri'], 'error.txt')
        progress_path = os.path.join(path, item['uri'], 'progress.txt')
        file_path = os.path.join(path, item['uri'], item['source'])

        # Check compressed file
        gunzip = ''
        if item['source'].endswith('.tar'):
            gunzip = f"| tar xO {item['selected']} 2> {error_path}"
        elif item['source'].endswith('.tar.gz'):
            gunzip = f"| tar zxO {item['selected']} 2> {error_path}"
        elif item['source'].endswith('.gz'):
            gunzip = f"| zcat 2> {error_path}"

        # Generate presigned-url for cloud mode
        if item['mode'] == 'cloud':
            client = boto3.client('s3', aws_access_key_id=item['access_key'], aws_secret_access_key=item['secret_key'])
            item['source'] = client.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': item['bucket'], 'Key': item['source']}, ExpiresIn=60)

        # MySQL & Aurora MySQL engines
        if server['engine'] in ('MySQL', 'Aurora MySQL'):
            if item['mode'] == 'file':
                command = f"echo 'RESTORE.{item['uri']}'; export MYSQL_PWD={server['password']}; pv -f --size {item['size']} -F '%p|%b|%r|%t|%e' {file_path} 2> {progress_path} {gunzip} | mysql -h{server['hostname']} -u{server['username']} {item['database']} 2> {error_path}"
            elif item['mode'] in ['url','cloud']:
                command = f"echo 'RESTORE.{item['uri']}' && export MYSQL_PWD={server['password']} && curl -sSL '{item['source']}' 2> {error_path} | pv -f --size {item['size']} -F '%p|%b|%r|%t|%e' 2> {progress_path} {gunzip} | mysql -h{server['hostname']} -u{server['username']} {item['database']} 2> {error_path}"

        # Start Import process
        p = core.execute(command)

        # Check if subprocess command has been killed (= stopped by user).
        status[0] = len(p['stderr']) > 0

    def __monitor(self, core, item, path, status):
        # Check if a stop it's been requested
        if not self.__alive(item):
            # SIGKILL
            command = f"ps -U $USER -u $USER u | grep 'RESTORE.{item['uri']}' | grep -v grep | awk '{{print $2}}' | xargs pkill -9 -P 2> /dev/null"
            core.execute(command)
            core.stop()
            return False

        # Init path vars
        progress_path = os.path.join(path, item['uri'], 'progress.txt')
        error_path = os.path.join(path, item['uri'], 'error.txt')

        # Read files
        p = core.execute(f"[ -f {progress_path} ] && tr '\r' '\n' < '{progress_path}' | sed '/^$/d' | tail -1")
        progress = self.__parse_progress(p['stdout']) if len(p['stdout']) > 0 else None

        p = core.execute(f"[ -f {error_path} ] && cat < {error_path}")
        error = self.__parse_error(p['stdout']) if len(p['stdout']) > 0 else None
        status[0] = error

        # Update restore with progress file
        query = """
            UPDATE `restore`
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
        # Upload file
        try:
            core.put(os.path.join(paths['local'], item['uri'], item['source']), os.path.join(paths['remote'], item['uri'], item['source']))
        except OSError:
            pass

    def __alive(self, item):
        # Check if process has been requested to be stopped
        query = """
            SELECT `stop`
            FROM `restore`
            WHERE `id` = %s
        """
        result = self._sql.execute(query, args=(item['id']))

        if len(result) == 0 or result[0]['stop'] == 1:
            query = """
                UPDATE `restore`
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

    def __parse_progress(self, string):
        if len(string) == 0:
            return None
        p = re.sub(' +', ' ', string)
        p = p[p.find(']')+1:]
        p = p.replace('\n','').replace('[','').replace(']','').strip()
        p = ' '.join([i.replace(' ', '') for i in p.split('|')]).strip()
        return p

    def __parse_error(self, string):
        if len(string) == 0:
            return None
        return string.strip()

    def __utcnow(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
