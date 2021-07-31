import os
import re
import time
import json
import shutil
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
        t = threading.Thread(target=self.__start, args=(user, item, server, base_path,))
        t.daemon = True
        t.start()
        t.join()

    def __start(self, user, item, server, base_path):
        # Start Import
        t = threading.Thread(target=self.__import, args=(item, server, base_path,))
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
            with open(error_path, 'r') as f:
                if len(f.read().strip()) > 0:
                    status = 'FAILED'
        query = """
            UPDATE `restore`
            SET
                `status` = %s,
                `ended` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(status, now, item['id']))

        # Remove execution folder from disk
        shutil.rmtree(os.path.join(base_path, item['uri']))

        # Send notification
        notification = {
            'name': "A restore has finished",
            'status': 'ERROR' if status == 'FAILED' else 'SUCCESS',
            'category': 'utils-restore',
            'data': '{{"id":"{}"}}'.format(item['id']),
            'date': self.__utcnow(),
            'show': 1
        }
        self._notifications.post(user_id=user['id'], notification=notification)

    def __import(self, item, server, base_path):
        # Build 'progress_path' & 'error_path'
        error_path = os.path.join(base_path, item['uri'], 'error.txt')
        progress_path = os.path.join(base_path, item['uri'], 'progress.txt')
        selected = ' '.join([i['file'] for i in json.loads(item['selected'])]) if item['selected'] is not None else ''
        size = sum(i['size'] for i in json.loads(item['selected'])) if item['selected'] is not None else item['size']

        # Start restore
        if server['engine'] in ('MySQL', 'Aurora MySQL'):
            gunzip = ''
            if item['source'].endswith('.tar'):
                gunzip = f'| tar xO {selected} 2> {error_path}'
            elif item['source'].endswith('.tar.gz'):
                gunzip = f'| tar zxO {selected} 2> {error_path}'
            elif item['source'].endswith('.gz'):
                gunzip = f'| gunzip -c 2> {error_path}'
            if item['mode'] == 'file':
                command = f"export MYSQL_PWD={server['password']}; pv -f --size {size} -F '%p|%b|%r|%t|%e' {os.path.join(base_path, item['uri'], item['source'])} 2> {progress_path} {gunzip} | mysql -h{server['hostname']} -u{server['username']} {item['database']} 2> {error_path}"
            elif item['mode'] == 'url':
                command = f"export MYSQL_PWD={server['password']}; curl -sSL '{item['source']}' 2> {error_path} | pv -f --size {size} -F '%p|%b|%r|%t|%e' 2> {progress_path} {gunzip} | mysql -h{server['hostname']} -u{server['username']} {item['database']} 2> {error_path}"

        p = subprocess.Popen(command, shell=True)

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

    def __monitor(self, item, base_path):
        # Init path vars
        progress_path = os.path.join(base_path, item['uri'], 'progress.txt')
        error_path = os.path.join(base_path, item['uri'], 'error.txt')

        # Read files
        progress = None
        if os.path.exists(progress_path):
            with open(progress_path, 'r') as f:
                progress = self.__parse_progress(f.read())

        error = None
        if os.path.exists(error_path):
            with open(error_path, 'r') as f:
                error = self.__parse_error(f.read())

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
