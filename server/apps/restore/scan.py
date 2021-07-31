import os
import re
import time
import shutil
import subprocess
import threading
from datetime import datetime

class Scan:
    def __init__(self, sql):
        self._sql = sql

    def start(self, item, base_path):
        # Start Process in another thread
        t = threading.Thread(target=self.__start, args=(item, base_path,))
        t.daemon = True
        t.start()
        # t.join() # <-- TO REMOVE !!!

    def metadata(self, item):
        # Get File Metadata
        p = subprocess.run(f"curl -sSLI '{item['source']}' | grep -E 'Content-Length:' | sort -k1 | awk '{{print $2}}'", shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if len(p.stdout) == 0 or int(p.stdout.split('\n')[0]) == 0:
            raise Exception("This URL is not valid")
        return { 'size': int(p.stdout.split('\n')[0]) }
        
    def __start(self, item, base_path):
        # Start Import
        t = threading.Thread(target=self.__scan, args=(item, base_path,))
        t.daemon = True
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
            UPDATE `restore_scans`
            SET `status` = IF(`status` = 'STOPPED', `status`, %s),
                `updated` = %s
            WHERE `id` = %s
        """
        self._sql.execute(query, args=(status, self.__utcnow(), item['id']))

        # Remove execution folder from disk
        # shutil.rmtree(os.path.join(base_path, item['uri']))

    def __scan(self, item, base_path):
        # Build 'progress_path' & 'error_path'
        error_path = os.path.join(base_path, item['uri'], 'error.txt')
        progress_path = os.path.join(base_path, item['uri'], 'progress.txt')
        data_path = os.path.join(base_path, item['uri'], 'data.txt')
        size = item['metadata']['size']

        # Start scan
        if item['source'].endswith('.tar'):
            tar = f'tar tv 2> {error_path}'
        elif item['source'].endswith('.tar.gz'):
            tar = f'tar ztv 2> {error_path}'
        elif item['source'].endswith('.tar.bz2'):
            tar = f'tar jtv 2> {error_path}'

        if item['mode'] == 'url':
            command = f"curl -sSL '{item['source']}' 2> {error_path} | pv -f --size {size} -F '%p|%b|%r|%t|%e' 2> {progress_path} | {tar} | awk '{{ print $6\"|\"$3; fflush() }}' > {data_path}"
        elif item['mode'] == 's3':
            pass

        p = subprocess.Popen(command, shell=True)

        # Add PID & started to the restore
        query = """
            UPDATE `restore_scans`
            SET
                `pid` = %s,
                `status` = 'IN PROGRESS',
                `updated` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(p.pid, now, item['id']))

        # Wait import to finish
        p.wait()

    def __monitor(self, item, base_path):
        # Init path vars
        progress_path = os.path.join(base_path, item['uri'], 'progress.txt')
        error_path = os.path.join(base_path, item['uri'], 'error.txt')
        data_path = os.path.join(base_path, item['uri'], 'data.txt')

        # Read progress log
        progress = None
        if os.path.exists(progress_path):
            # p = subprocess.run(f"tr '\r' '\n' < '{progress_path}' | xargs | tail -1", shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p = subprocess.run(f"tr '\r' '\n' < '{progress_path}' | tail -1", shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            progress = self.__parse_progress(p.stdout) if len(p.stdout) > 0 else None

        # Read error log
        error = None
        if os.path.exists(error_path):
            with open(error_path, 'r') as f:
                error = self.__parse_error(f.read())

        # Read data log
        data = None
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                data = self.__parse_data(f.read())

        # Update restore with progress file
        query = """
            UPDATE `restore_scans`
            SET 
                `progress` = %s,
                `error` = %s,
                `data` = %s,
                `updated` = %s
            WHERE `id` = %s
        """
        now = self.__utcnow()
        self._sql.execute(query, args=(progress, error, data, now, item['id']))

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

    def __parse_data(self, string):
        if len(string) == 0:
            return None
        return string.strip()

    def __utcnow(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
