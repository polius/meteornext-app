import os
# import sys
import json
import time
import uuid
import random
import socket
import schedule
import threading
from multiprocessing import Process
from datetime import datetime, timedelta

import routes.deployments.deployments
import routes.utils.utils
import apps.monitor.monitor
import apps.imports.scan

class Cron:
    def __init__(self, app, license, sql):
        self._app = app
        self._license = license
        self._sql = sql
        self._node = str(uuid.uuid4())
        self._locks = {"executions": False, "deployments_monitor": False, "monitoring": False, "utils_queue": False, "utils_scans": False, "check_nodes": False, "client_clean": False}
        self._current_pid = os.getpid()
        self.__start()

    def __start(self):
        # One Time Tasks
        # self.__run_threaded(self.__monitoring)
        # Scheduled Tasks
        schedule.every(10).seconds.do(self.__run_threaded, self.__executions)
        schedule.every(10).seconds.do(self.__run_threaded, self.__deployments_monitor)
        schedule.every(10).seconds.do(self.__run_threaded, self.__monitoring)
        schedule.every(10).seconds.do(self.__run_threaded, self.__utils_queue)
        schedule.every(10).seconds.do(self.__run_threaded, self.__utils_scans)
        schedule.every(10).seconds.do(self.__run_threaded, self.__check_nodes)
        schedule.every().hour.do(self.__run_threaded, self.__client_clean)
        schedule.every().hour.do(self.__run_threaded, self.__monitoring_clean)
        schedule.every().hour.do(self.__run_threaded, self.__import_clean)
        schedule.every().hour.do(self.__run_threaded, self.__logs)
        schedule.every().day.do(self.__run_threaded, self.__check_license)
        schedule.every().day.at("00:00").do(self.__run_threaded, self.__coins)

        # Start Cron Listener
        t = threading.Thread(target=self.__run_schedule)
        t.daemon = True
        t.start()

    def __run_threaded(self, job_func):
        t = threading.Thread(target=job_func)
        t.daemon = True
        t.start()

    def __run_schedule(self):
        while True:
            if os.getpid() == self._current_pid:
                schedule.run_pending()
            time.sleep(1)

    def __check_nodes(self):
        # Check lock
        if self._locks['check_nodes']:
            return

        # Bind lock
        self._locks['check_nodes'] = True

        try:
            # Determine master & worker nodes
            connection, cursor = self._sql.raw()
            connection.begin()
            try:
                ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                ip = None
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            last_minute = (datetime.utcnow() - timedelta(seconds = 30)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT * FROM nodes FOR UPDATE")
            nodes = cursor.fetchall()
            if len(nodes) == 0:
                cursor.execute("INSERT INTO `nodes`(`id`,`type`,`ip`,`healthcheck`) VALUES (%s,'master',%s,%s)", (self._node, ip, now))
            else:
                master = [i for i in nodes if i['type'] == 'master'][0]
                current = [i for i in nodes if i['id'] == self._node]
                # The current node is a worker
                if len(current) == 0 or current[0]['type'] == 'worker':
                    cursor.execute("INSERT INTO `nodes`(`id`,`type`,`ip`,`healthcheck`) VALUES (%s,'worker',%s,%s) ON DUPLICATE KEY UPDATE `healthcheck` = VALUES(`healthcheck`)", (self._node, ip, now))
                    # Check if the node has to be promoted
                    if master['healthcheck'] < datetime.strptime(last_minute, "%Y-%m-%d %H:%M:%S"):
                        cursor.execute("UPDATE `nodes` SET `type` = IF(`id` = %s,'master','worker')", (self._node))
                        cursor.execute("DELETE FROM `nodes` WHERE `healthcheck` < %s", (last_minute))
                # The current node is the master
                else:
                    cursor.execute("UPDATE `nodes` SET `healthcheck` = %s WHERE id = %s", (now, self._node))
                    cursor.execute("DELETE FROM `nodes` WHERE `healthcheck` < %s", (last_minute))

            # Commit transaction
            cursor.close()
            connection.commit()
        finally:
            # Free lock
            self._locks['check_nodes'] = False

    def __executions(self):
        # Check license
        if not self._license.validated:
            return

        # Check lock
        if self._locks['executions']:
            return

        # Bind lock
        self._locks['executions'] = True

        try:
            # Check master node
            result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Check new scheduled & queued executions
            deployments = routes.deployments.deployments.Deployments(self._app, self._sql, self._license)
            deployments.check_finished()
            deployments.check_recurring()
            deployments.check_scheduled()
            deployments.check_queued()
        finally:
            # Free lock
            self._locks['executions'] = False

    def __deployments_monitor(self):
        # Check license
        if not self._license.validated:
            return

        # Check lock
        if self._locks['deployments_monitor']:
            return

        # Bind lock
        self._locks['deployments_monitor'] = True

        try:
            # Check master node
            result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Check alive processes
            result = self._sql.execute(query="SELECT id, pid FROM executions WHERE status IN ('IN PROGRESS','STOPPING')")
            recheck = []
            for i in result:
                if not os.path.exists(f"/proc/{i['pid']}"):
                    recheck.append(i['id'])

            if len(recheck) > 0:
                # Wait some time to double verify
                time.sleep(60)
                result = self._sql.execute(query=f"SELECT id, pid, progress FROM executions WHERE status IN ('IN PROGRESS','STOPPING') AND id IN({','.join(['%s'] * len(recheck))})", args=(recheck))
                for i in result:
                    if not os.path.exists(f"/proc/{i['pid']}"):
                        # Update execution status and progres
                        progress = json.loads(i['progress'])
                        progress['error'] = "The execution has been interrupted. There is not enough memory available to run this deployment."
                        self._sql.execute(query="UPDATE executions SET status = 'FAILED', error = 1, progress = %s WHERE id = %s", args=(json.dumps(progress), i['id']))
        finally:
            # Free lock
            self._locks['deployments_monitor'] = False

    def __utils_queue(self):
        # Check license
        if not self._license.validated:
            return

        # Check lock
        if self._locks['utils_queue']:
            return

        # Bind lock
        self._locks['utils_queue'] = True

        try:
            # Check master node
            result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Check queued executions
            utils = routes.utils.utils.Utils(self._app, self._sql, self._license)
            utils.check_queued()
        finally:
            # Free lock
            self._locks['utils_queue'] = False

    def __check_license(self):
        # Check if the license is still active
        time.sleep(random.randint(1,1800))
        self._license.validate(force=True)

    def __coins(self):
        # Check license
        if not self._license.validated:
            return

        # Check master node
        result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
        if len(result) == 0 or result[0]['type'] != 'master':
            return

        # Hand out coins for all users
        query = """
            UPDATE users u
            JOIN groups g ON g.id = u.group_id
            SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
        """
        self._sql.execute(query)

    def __logs(self):
        # Check license
        if not self._license.validated:
            return

        # Check master node
        result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
        if len(result) == 0 or result[0]['type'] != 'master':
            return

        # Get setting values
        setting = self._sql.execute("SELECT value FROM settings WHERE name = 'FILES'")
        files = json.loads(setting[0]['value'])

        # Expire deployments
        query = """
            SELECT e.id, e.uri
            FROM executions e
            JOIN deployments d ON d.id = e.deployment_id
            JOIN users u ON u.id = d.user_id
            JOIN groups g ON g.id = u.group_id
            WHERE g.deployments_expiration_days != 0
            AND DATE_ADD(DATE(e.created), INTERVAL g.deployments_expiration_days DAY) <= CURRENT_DATE
            AND e.uri IS NOT NULL
            AND e.expired = 0
        """
        expired = self._sql.execute(query)

        for i in expired:
            # DISK
            path = os.path.join(files['path'], 'deployments', i['uri'])
            if os.path.isfile(path + '.json'):
                os.remove(path + '.json')
            # SQL
            self._sql.execute(query="UPDATE executions SET expired = 1 WHERE id = %s", args=(i['id']))

    def __monitoring(self):
        # Check license
        if not self._license.validated:
            return

        # Check lock
        if self._locks['monitoring']:
            return

        # Bind lock
        self._locks['monitoring'] = True

        try:
            # Check master node
            result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Start monitoring servers
            monitoring = apps.monitor.monitor.Monitor(self._license, self._sql.config)
            p = threading.Thread(target=monitoring.start)
            p.daemon = True
            p.start()
            p.join()

            # base_path = sys._MEIPASS if self._bin else self._app.root_path
            # path = f"{base_path}/apps/monitor/init" if self._bin else f"python3 {base_path}/../monitor/monitor.py"
            # config_path = "/root/server.conf".format(base_path) if self._bin else "{}/server.conf".format(base_path)

            # Build Command
            # command = f"{path} --conf '{config_path}' --resources '{self._license.resources}'"
            # if self._license.status['sentry']:
            #     command += f" --sentry '{self._license.status['sentry']}'"

            # Execute Monitor
            # os.system(command + ' &')
        finally:
            # Free lock
            self._locks['monitoring'] = False

    def __monitoring_clean(self):
        # Check license
        if not self._license.validated:
            return

        # Check master node
        result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
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
        self._sql.execute(query)

        query = """
            DELETE ms
            FROM monitoring_servers ms
            LEFT JOIN monitoring m ON m.server_id = ms.server_id
            WHERE m.server_id IS NULL
        """
        self._sql.execute(query)

        # Clean monitoring events
        query = """
            DELETE FROM monitoring_events
            WHERE DATE_ADD(`time`, INTERVAL 15 DAY) < %s
        """
        self._sql.execute(query, args=(utcnow))

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
        self._sql.execute(query=query, args=(utcnow))

    def __import_clean(self):
        # Check license
        if not self._license.validated:
            return

        # Check master node
        result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
        if len(result) == 0 or result[0]['type'] != 'master':
            return

        # Clean unfinished imports
        query = """
            DELETE FROM imports_scans
            WHERE `status` != 'IN PROGRESS'
            AND DATE_ADD(`updated`, INTERVAL 1 DAY) <= CURRENT_DATE
        """
        self._sql.execute(query)

    def __client_clean(self):
        # Check license
        if not self._license.validated:
            return

        # Check lock
        if self._locks['client_clean']:
            return

        # Bind lock
        self._locks['client_clean'] = True

        try:
            # Check master node
            result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Clean tracked queries
            query = """
                DELETE cq
                FROM client_queries cq
                JOIN users u ON u.id = cq.user_id
                JOIN groups g ON g.id = u.group_id
                WHERE DATE_ADD(DATE(cq.date), INTERVAL g.client_tracking_retention DAY) <= CURRENT_DATE
            """
            self._sql.execute(query)
        finally:
            # Free lock
            self._locks['client_clean'] = False

    def __utils_scans(self):
        try:
            # Check lock
            if self._locks['utils_scans']:
                return

            # Bind lock
            self._locks['utils_scans'] = True

            # Check license
            if not self._license.validated:
                return

            # Check master node
            result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
            if len(result) == 0 or result[0]['type'] != 'master':
                return

            # Stop all scans not being tracked by the user
            query = """
                SELECT id, pid
                FROM imports_scans
                WHERE status = 'IN PROGRESS'
                AND TIMESTAMPDIFF(SECOND, `readed`, `updated`) >= 10
            """
            result = self._sql.execute(query)
            scan = apps.imports.scan.Scan(self._sql)
            for i in result:
                query = "UPDATE imports_scans SET status = 'STOPPED' WHERE id = %s"
                self._sql.execute(query, (i['id']))
                scan.stop(i['pid'])
        finally:
            # Free lock
            self._locks['utils_scans'] = False
