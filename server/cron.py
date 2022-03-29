import os
import json
import time
import uuid
import random
import socket
import schedule
import threading
from datetime import datetime, timedelta

import routes.deployments.deployments
import routes.utils.utils
import apps.monitoring.monitoring
import apps.imports.scan

class Cron:
    def __init__(self, app, license, sql):
        self._app = app
        self._license = license
        self._sql = sql
        self._node = str(uuid.uuid4())

        @app.before_first_request
        def start():
            # Scheduled Tasks
            schedule.every(30).seconds.do(self.__run_threaded, self.__check_nodes)
            schedule.every(10).seconds.do(self.__run_threaded, self.__executions)
            schedule.every(10).seconds.do(self.__run_threaded, self.__utils_queue)
            schedule.every(10).seconds.do(self.__run_threaded, self.__monitoring)
            schedule.every().day.do(self.__run_threaded, self.__check_license)
            schedule.every().day.at("00:00").do(self.__run_threaded, self.__coins)
            schedule.every().day.at("00:00").do(self.__run_threaded, self.__logs)
            schedule.every().day.at("00:00").do(self.__run_threaded, self.__monitoring_clean)
            schedule.every().day.at("00:00").do(self.__run_threaded, self.__import_clean)
            schedule.every().hour.do(self.__run_threaded, self.__client_clean)
            schedule.every(10).seconds.do(self.__run_threaded, self.__utils_scans)

            # Start Cron Listener
            t = threading.Thread(target=self.__run_schedule)
            t.start()

    def __run_threaded(self, job_func):
        job_thread = threading.Thread(target=job_func)
        job_thread.start()

    def __run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __check_nodes(self):
        # Determine master & worker nodes            
        connection, cursor = self._sql.raw()
        connection.begin()
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = None
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        last_minute = (datetime.utcnow() - timedelta(seconds = 60)).strftime("%Y-%m-%d %H:%M:%S")
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

    def __executions(self):
        if not self._license.validated:
            return

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

    def __utils_queue(self):
        if not self._license.validated:
            return

        # Check master node
        result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
        if len(result) == 0 or result[0]['type'] != 'master':
            return

        # Check queued executions
        utils = routes.utils.utils.Utils(self._app, self._sql, self._license)
        utils.check_queued()

    def __check_license(self):
        # Check if the license is still active
        time.sleep(random.randint(1,1800))
        self._license.validate(force=True)

    def __coins(self):
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
        if not self._license.validated:
            return

        # Check master node
        result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
        if len(result) == 0 or result[0]['type'] != 'master':
            return

        # Clean monitoring servers
        monitoring = apps.monitoring.monitoring.Monitoring(self._license, self._sql)
        monitoring.start()

    def __monitoring_clean(self):
        if not self._license.validated:
            return

        # Check master node
        result = self._sql.execute(query="SELECT type FROM nodes WHERE id = %s", args=(self._node))
        if len(result) == 0 or result[0]['type'] != 'master':
            return

        # Clean monitoring servers
        monitoring = apps.monitoring.monitoring.Monitoring(self._license, self._sql)
        monitoring.clean()

    def __import_clean(self):
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
        if not self._license.validated:
            return

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

    def __utils_scans(self):
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
