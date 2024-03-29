import os
import sys
import json
import time
import queue
import traceback
import random
import socket
import schedule
import threading
import sentry_sdk
from signal import SIGHUP
from datetime import datetime, timedelta

import connectors.base
import apps.monitor.monitor
import apps.imports.scan

class Cron:
    def __init__(self, license, sentry_dsn, node):
        self._sql = None
        self._license = license
        self._node = node
        self._sentry = None
        self._locks = {"deployments_monitor": False, "utils_scans": False, "check_nodes": False, "client_clean": False}
        self._queue = queue.Queue()
        # Retrieve base path
        self._bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._base_path = os.path.realpath(os.path.dirname(sys.executable)) if self._bin else os.path.realpath(os.path.dirname(sys.argv[0]))
        # Check if the Api process has been started and the license is active 
        self.__check(sentry_dsn)
        # Start the Cron engine
        self.__start()

    def __check(self, sentry_dsn):
        # Redirect stderr to file
        if self._bin:
            sys.stderr = open(f'{self._base_path}/cron.err', 'w')

        # Check if 'server.conf' file exists and license is valid
        while not os.path.exists(f"{self._base_path}/server.conf") or not self._license.is_validated():
            time.sleep(1)

        # Load 'server.conf' file
        with open(f"{self._base_path}/server.conf") as file_open:
            conf = json.load(file_open)
            self._sql = {"sql": conf['sql']}

        # Init sentry
        self._sentry = {"enabled": self._license.get_status()['sentry'], "environment": conf['license']['access_key'], "dsn": sentry_dsn}
        if self._sentry['enabled']:
            sentry_sdk.init(dsn=self._sentry['dsn'], environment=self._sentry['environment'], traces_sample_rate=0)

    def __start(self):
        # Scheduled Tasks
        schedule.every(10).seconds.do(self._queue.put, self.__deployments_monitor)
        schedule.every(10).seconds.do(self._queue.put, self.__utils_scans)
        schedule.every(10).seconds.do(self._queue.put, self.__check_nodes)
        schedule.every().minute.at(":00").do(self._queue.put, self.__advanced_memory)
        schedule.every().hour.do(self._queue.put, self.__client_clean)
        schedule.every().hour.do(self._queue.put, self.__monitoring_clean)
        schedule.every().hour.do(self._queue.put, self.__import_clean)
        schedule.every().hour.do(self._queue.put, self.__logs)
        schedule.every().day.do(self._queue.put, self.__check_license)
        schedule.every().day.at("00:00").do(self._queue.put, self.__coins)

        t = threading.Thread(target=self.__worker_main)
        t.daemon = True
        t.start()

        while 1:
            schedule.run_pending()
            time.sleep(1)

    def __worker_main(self):
        while 1:
            job_func = self._queue.get()
            try:
                job_func()
            except Exception as e:
                traceback.print_exc()
                if self._sentry['enabled']:
                    sentry_sdk.capture_exception(e)
                    sentry_sdk.flush()
            finally:
                self._queue.task_done()

    def __check_nodes(self):
        # Check lock
        if self._locks['check_nodes']:
            return

        # Bind lock
        self._locks['check_nodes'] = True

        try:
            # Init SQL Connection
            conn = connectors.base.Base(self._sql)

            # Determine master & worker nodes
            try:
                ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                ip = None
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            last_minute = (datetime.utcnow() - timedelta(seconds = 30)).strftime("%Y-%m-%d %H:%M:%S")
            nodes = conn.execute("SELECT * FROM nodes FOR UPDATE")
            if len(nodes) == 0:
                conn.execute("INSERT INTO `nodes`(`id`,`type`,`ip`,`pid`,`healthcheck`) VALUES (%s,'master',%s,%s,%s)", (self._node, ip, os.getpid(), now))
            else:
                master = [i for i in nodes if i['type'] == 'master'][0]
                current = [i for i in nodes if i['id'] == self._node]
                # The current node is a worker
                if len(current) == 0 or current[0]['type'] == 'worker':
                    conn.execute("INSERT INTO `nodes`(`id`,`type`,`ip`,`pid`,`healthcheck`) VALUES (%s,'worker',%s,%s,%s) ON DUPLICATE KEY UPDATE `healthcheck` = VALUES(`healthcheck`)", (self._node, ip, os.getpid(), now))
                    # Check if the node has to be promoted
                    if master['healthcheck'] < datetime.strptime(last_minute, "%Y-%m-%d %H:%M:%S"):
                        conn.execute("UPDATE `nodes` SET `type` = IF(`id` = %s,'master','worker')", (self._node))
                        conn.execute("DELETE FROM `nodes` WHERE `healthcheck` < %s", (last_minute))
                # The current node is the master
                else:
                    conn.execute("UPDATE `nodes` SET `pid` = %s, `healthcheck` = %s WHERE id = %s", (os.getpid(), now, self._node))
                    conn.execute("DELETE FROM `nodes` WHERE `healthcheck` < %s", (last_minute))
        finally:
            # Close SQL Connection
            conn.stop()
            # Free lock
            self._locks['check_nodes'] = False

    def __deployments_monitor(self):
        # Check license
        if not self._license.is_validated():
            return

        # Check lock
        if self._locks['deployments_monitor']:
            return

        # Bind lock
        self._locks['deployments_monitor'] = True

        try:
            # Init SQL Connection
            conn = connectors.base.Base(self._sql)

            # Check master node
            result = conn.execute(query="SELECT type, pid FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Check alive processes
            result = conn.execute(query="SELECT id, pid FROM executions WHERE status IN ('IN PROGRESS','STOPPING')")
            recheck = []
            for i in result:
                if not os.path.exists(f"/proc/{i['pid']}"):
                    recheck.append(i['id'])

            if len(recheck) > 0:
                # Wait some time to double verify
                time.sleep(300)
                result = conn.execute(query=f"SELECT id, pid, progress FROM executions WHERE status IN ('IN PROGRESS','STOPPING') AND id IN({','.join(['%s'] * len(recheck))})", args=(recheck))
                for i in result:
                    if not os.path.exists(f"/proc/{i['pid']}"):
                        # Update execution status and progres
                        progress = json.loads(i['progress'])
                        progress['error'] = "The execution has been interrupted. There might not be enough memory available to run this deployment."
                        conn.execute(query="UPDATE executions SET status = 'FAILED', error = 1, progress = %s, ended = %s WHERE id = %s", args=(json.dumps(progress), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), i['id']))
        finally:
            # Close SQL Connection
            conn.stop()
            # Free lock
            self._locks['deployments_monitor'] = False

    def __check_license(self):
        # Check if the license is still active
        time.sleep(random.randint(1,1800))
        self._license.validate(force=True)

    def __coins(self):
        # Check license
        if not self._license.is_validated():
            return

        try:
            # Init SQL Connection
            conn = connectors.base.Base(self._sql)

            # Check master node
            result = conn.execute(query="SELECT type, pid FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Hand out coins for all users
            query = """
                UPDATE users u
                JOIN `groups` g ON g.id = u.group_id
                SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
            """
            conn.execute(query)
        finally:
            # Close SQL Connection
            conn.stop()

    def __logs(self):
        # Check license
        if not self._license.is_validated():
            return

        try:
            # Init SQL Connection
            conn = connectors.base.Base(self._sql)

            # Check master node
            result = conn.execute(query="SELECT type, pid FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Expire deployments
            query = """
                SELECT e.id, e.uri
                FROM executions e
                JOIN deployments d ON d.id = e.deployment_id
                JOIN users u ON u.id = d.user_id
                JOIN `groups` g ON g.id = u.group_id
                WHERE g.deployments_expiration_days != 0
                AND DATE_ADD(DATE(e.created), INTERVAL g.deployments_expiration_days DAY) <= CURRENT_DATE
                AND e.uri IS NOT NULL
                AND e.expired = 0
            """
            expired = conn.execute(query)

            for i in expired:
                # DISK
                path = f"{self._base_path}/files/deployments/{i['uri']}"
                if os.path.isfile(path + '.json.gz'):
                    os.remove(path + '.json.gz')
                # SQL
                conn.execute(query="UPDATE executions SET expired = 1 WHERE id = %s", args=(i['id']))
        finally:
            # Close SQL Connection
            conn.stop()

    def __monitoring_clean(self):
        # Check license
        if not self._license.is_validated():
            return

        try:
            # Init SQL Connection
            conn = connectors.base.Base(self._sql)

            # Check master node
            result = conn.execute(query="SELECT type, pid FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Clean monitoring servers
            utcnow = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            query = """
                DELETE m
                FROM monitoring m
                WHERE monitor_enabled = 0
                AND parameters_enabled = 0
                AND processlist_enabled = 0
                AND queries_enabled = 0
            """
            conn.execute(query)

            query = """
                DELETE ms
                FROM monitoring_servers ms
                LEFT JOIN monitoring m ON m.server_id = ms.server_id
                WHERE m.server_id IS NULL
            """
            conn.execute(query)

            # Clean monitoring events
            query = """
                DELETE FROM monitoring_events
                WHERE DATE_ADD(`time`, INTERVAL 15 DAY) < %s
            """
            conn.execute(query, args=(utcnow))

            # Clean queries that exceeds the MAX defined data retention
            query = """
                DELETE q
                FROM monitoring_queries q
                LEFT JOIN
                (
                    SELECT m.server_id, MAX(s.query_data_retention) AS 'data_retention'
                    FROM monitoring_settings s
                    JOIN monitoring m ON m.user_id = s.user_id
                    GROUP BY m.server_id
                ) t ON t.server_id = q.server_id
                WHERE t.server_id IS NULL
                OR DATE_ADD(q.first_seen, INTERVAL t.data_retention DAY) <= %s
            """
            conn.execute(query=query, args=(utcnow))
        finally:
            # Close SQL Connection
            conn.stop()

    def __import_clean(self):
        # Check license
        if not self._license.is_validated():
            return

        try:
            # Init SQL Connection
            conn = connectors.base.Base(self._sql)

            # Check master node
            result = conn.execute(query="SELECT type, pid FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Clean unfinished imports
            query = """
                DELETE FROM imports_scans
                WHERE `status` != 'IN PROGRESS'
                AND DATE_ADD(`updated`, INTERVAL 1 DAY) <= CURRENT_DATE
            """
            conn.execute(query)
        finally:
            # Close SQL Connection
            conn.stop()

    def __client_clean(self):
        # Check license
        if not self._license.is_validated():
            return

        # Check lock
        if self._locks['client_clean']:
            return

        # Bind lock
        self._locks['client_clean'] = True

        try:
            # Init SQL Connection
            conn = connectors.base.Base(self._sql)

            # Check master node
            result = conn.execute(query="SELECT type, pid FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Clean tracked queries
            query = """
                DELETE cq
                FROM client_queries cq
                JOIN users u ON u.id = cq.user_id
                JOIN `groups` g ON g.id = u.group_id
                WHERE DATE_ADD(DATE(cq.end_date), INTERVAL g.client_tracking_retention DAY) <= CURRENT_DATE
            """
            conn.execute(query)
        finally:
            # Close SQL Connection
            conn.stop()
            # Free lock
            self._locks['client_clean'] = False

    def __utils_scans(self):
        # Check license
        if not self._license.is_validated():
            return

        # Check lock
        if self._locks['utils_scans']:
            return

        # Bind lock
        self._locks['utils_scans'] = True

        try:
            # Init SQL Connection
            conn = connectors.base.Base(self._sql)

            # Check master node
            result = conn.execute(query="SELECT type, pid FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Stop all scans not being tracked by the user
            query = """
                SELECT id, pid
                FROM imports_scans
                WHERE status = 'IN PROGRESS'
                AND TIMESTAMPDIFF(SECOND, `readed`, `updated`) >= 10
            """
            result = conn.execute(query)
            scan = apps.imports.scan.Scan(conn)
            for i in result:
                query = "UPDATE imports_scans SET status = 'STOPPED' WHERE id = %s"
                conn.execute(query, (i['id']))
                scan.stop(i['pid'])

        finally:
            # Close SQL Connection
            conn.stop()
            # Free lock
            self._locks['utils_scans'] = False

    def __advanced_memory(self):
        # Check license and environment
        if not self._license.is_validated():
            return

        try:
            # Init SQL Connection
            conn = connectors.base.Base(self._sql)

            # Check master node
            result = conn.execute(query="SELECT type, pid FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Get current day and current time
            DAYS = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
            current_day = DAYS[datetime.today().strftime('%A')]
            current_time = datetime.utcnow().strftime('%H:%M')

            # Get setting values
            setting = conn.execute("SELECT value FROM settings WHERE name = 'ADVANCED'")
            advanced = json.loads(setting[0]['value'])

            # Restart worker
            if advanced['memory_enabled'] and current_day in advanced['memory_days'] and advanced['memory_time'] == current_time:
                with open(f'{self._base_path}/server.pid', 'r') as fopen:
                    pid = int(fopen.read())
                    # Kill zombie workers
                    os.system(f"for i in $(ps -p $(pgrep -d, -u $(whoami) -P {pid}) --sort=start | grep 'init\|python' | awk '{{print $1}}' | head -n -1); do kill -9 $i; done")
                    # Spawn a new worker and close the old one
                    os.kill(pid, SIGHUP)

        finally:
            # Close SQL Connection
            conn.stop()
