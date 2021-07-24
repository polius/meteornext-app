import os
import re
import time
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
        t.start()

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
            'name': "Restore '{}' has finished".format(item['name']),
            'status': 'ERROR' if status == 'FAILED' else 'SUCCESS',
            'category': 'utils-restore',
            'data': '{{"id":"{}"}}'.format(item['id']),
            'date': self.__utcnow(),
            'show': 1
        }
        self._notifications.post(user_id=user['id'], notification=notification)

    def __import(self, item, server, base_path):
        if item['mode'] == 'file':
            self.__import_file(item, server, base_path)
        elif item['mode'] == 'url':
            pass
        elif item['mode'] == 's3':
            pass

    def __import_file(self, item, server, base_path):
        # Build 'progress_path' & 'error_path'
        error_path = os.path.join(base_path, item['uri'], 'error.txt')
        progress_path = os.path.join(base_path, item['uri'], 'progress.txt')

        # Start restore
        if server['engine'] in ('MySQL', 'Aurora MySQL'):
            zcat = f'| zcat 2> {error_path}' if not item['file'].endswith('.sql') else ''
            command = f"export MYSQL_PWD={server['password']}; pv -fF '%p %b %r %t %e' {os.path.join(base_path, item['uri'], item['file'])} 2> {progress_path} {zcat} | mysql -h{server['hostname']} -u{server['username']} {item['database']} 2> {error_path}"
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
        return re.sub(' +', ' ', p)

    def __parse_error(self, string):
        if len(string) == 0:
            return None
        return string.strip()

    def __utcnow(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
