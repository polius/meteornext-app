import os
import re
import time
import boto3
import shutil
import psutil
import signal
import subprocess
import threading
from datetime import datetime

import models.notifications

class Restore:
    def __init__(self, sql):
        self._sql = sql
        self._notifications = models.notifications.Notifications(sql)

    def start(self, user, item, server, base_path):
        # Start Process in another thread
        t = threading.Thread(target=self.__core, args=(user, item, server, base_path,))
        t.daemon = True
        t.start()

    def stop(self, pid):
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for process in children:
            try:
                process.send_signal(signal.SIGKILL)
            except Exception:
                pass

    def __core(self, user, item, server, base_path):
        # Start Import
        stopped = [False]
        t = threading.Thread(target=self.__import, args=(item, server, base_path, stopped,))
        t.start()

        # Start Monitor
        while t.is_alive():
            self.__monitor(item, base_path)
            time.sleep(1)
        self.__monitor(item, base_path)

        # Update restore status
        error_path = os.path.join(base_path, item['uri'], 'error.txt')
        status = 'SUCCESS'
        if os.path.exists(error_path):
            with open(error_path, 'rb') as f:
                if len(f.read().decode('utf-8','ignore').strip()) > 0:
                    status = 'FAILED'
        query = """
            UPDATE `restore`
            SET
                `status` = IF(`status` = 'STOPPED', 'STOPPED', %s),
                `ended` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(status, now, item['id']))

        # Remove execution folder from disk
        shutil.rmtree(os.path.join(base_path, item['uri']))

        # Send notification
        if not stopped[0]:
            notification = {
                'name': f"A restore has finished",
                'status': 'ERROR' if status == 'FAILED' else 'SUCCESS',
                'category': 'utils-restore',
                'data': '{{"id":"{}"}}'.format(item['id']),
                'date': self.__utcnow(),
                'show': 1
            }
            self._notifications.post(user_id=user['id'], notification=notification)

    def __import(self, item, server, base_path, stopped):
        # Build 'progress_path' & 'error_path'
        error_path = os.path.join(base_path, item['uri'], 'error.txt')
        progress_path = os.path.join(base_path, item['uri'], 'progress.txt')

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
                command = f"export MYSQL_PWD={server['password']}; pv -f --size {item['size']} -F '%p|%b|%r|%t|%e' {os.path.join(base_path, item['uri'], item['source'])} 2> {progress_path} {gunzip} | mysql -h{server['hostname']} -u{server['username']} {item['database']} 2> {error_path}"
            elif item['mode'] in ['url','cloud']:
                command = f"export MYSQL_PWD={server['password']}; curl -sSL '{item['source']}' 2> {error_path} | pv -f --size {item['size']} -F '%p|%b|%r|%t|%e' 2> {progress_path} {gunzip} | mysql -h{server['hostname']} -u{server['username']} {item['database']} 2> {error_path}"

        # Start Import process
        p = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)

        # Add PID & started to the restore
        query = """
            UPDATE `restore`
            SET
                `pid` = %s,
                `status` = 'IN PROGRESS',
                `started` = %s,
                `updated` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(p.pid, now, now, item['id']))

        # Wait import to finish
        p.wait()

        # Check if subprocess command has been killed (= stopped by user).
        stopped[0] = len(p.stderr.readlines()) > 0

    def __monitor(self, item, base_path):
        # Init path vars
        progress_path = os.path.join(base_path, item['uri'], 'progress.txt')
        error_path = os.path.join(base_path, item['uri'], 'error.txt')

        # Read files
        progress = None
        if os.path.exists(progress_path):
            p = subprocess.run(f"tr '\r' '\n' < '{progress_path}' | sed '/^$/d' | tail -1", shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            progress = self.__parse_progress(p.stdout) if len(p.stdout) > 0 else None

        error = None
        if os.path.exists(error_path):
            with open(error_path, 'rb') as f:
                error = self.__parse_error(f.read().decode('utf-8','ignore'))

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
