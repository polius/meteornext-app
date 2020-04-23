import os
import sys
import json
import time
import schedule
import threading

import routes.deployments.deployments
import routes.deployments.views.basic
import routes.deployments.views.pro
import routes.deployments.views.inbenta

import apps.monitoring.monitoring

class Cron:
    def __init__(self, app, license, blueprints, sql):
        self._app = app
        self._license = license
        self._sql = sql
        self._monitoring_ready = True

    def start(self):
        # Init Crons
        schedule.every(10).seconds.do(self.__executions)
        schedule.every().day.at("00:00").do(self.__coins)
        schedule.every().day.at("00:00").do(self.__logs)
        schedule.every(1).seconds.do(self.__monitoring)

        # Start Cron Listener
        t = threading.Thread(target=self.__run_schedule)
        t.start()

    def __run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __executions(self):
        # Basic Deployments
        basic = routes.deployments.views.basic.Basic(self._app, self._sql, self._license)
        basic.check_finished()
        basic.check_scheduled()

        # Pro Deployments
        pro = routes.deployments.views.pro.Pro(self._app, self._sql, self._license)
        pro.check_finished()
        pro.check_scheduled()

        # Inbenta Deployments
        inbenta = routes.deployments.views.inbenta.Inbenta(self._app, self._sql, self._license)
        inbenta.check_finished()
        inbenta.check_scheduled()

        # Deployments
        deployments = routes.deployments.deployments.Deployments(self._app, self._sql, self._license)
        deployments.check_queued()

    def __coins(self):
        if not self._license.validated:
            return
        print("- Giving coins...")
        query = """
            UPDATE users u
            JOIN groups g ON g.id = u.group_id
            SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
        """
        self._sql.execute(query)

    def __logs(self):
        if not self._license.validated:
            return
        print("- Cleaning logs...")
        # Get expiration value
        setting = self._sql.execute("SELECT value FROM settings WHERE name = 'LOGS'")

        # Check expiration is active
        if len(setting) > 0:
            setting = json.loads(setting[0]['value'])
            if 'expire' in setting['local'] and setting['local']['expire'] is not None:
                query = """
                    SELECT id, uri, 'basic' AS 'mode'
                    FROM deployments_basic
                    WHERE DATE_ADD(DATE(created), INTERVAL {0} DAY) <= CURRENT_DATE
                    AND expired = 0
                    UNION ALL
                    SELECT id, uri, 'pro' AS 'mode'
                    FROM deployments_pro
                    WHERE DATE_ADD(DATE(created), INTERVAL {0} DAY) <= CURRENT_DATE
                    AND expired = 0
                    UNION ALL
                    SELECT id, uri, 'inbenta' AS 'mode'
                    FROM deployments_inbenta
                    WHERE DATE_ADD(DATE(created), INTERVAL {0} DAY) <= CURRENT_DATE
                    AND expired = 0
                """.format(setting['local']['expire'])
                expired = self._sql.execute(query)

                # Expire deployments
                for i in expired:
                    # DISK
                    execution_path = '{}/{}'.format(setting['local']['path'], i['uri'])
                    if os.path.isfile(execution_path + '.tar.gz'):
                        os.remove(execution_path + '.tar.gz')
                    if os.path.isfile(execution_path + '.js'):
                        os.remove(execution_path + '.js')
                    # SQL
                    self._sql.execute("UPDATE deployments_{} SET expired = 1 WHERE id = {}".format(i['mode'], i['id']))

    def __monitoring(self):
        if self._monitoring_ready:
            self._monitoring_ready = False
            monitoring = apps.monitoring.monitoring.Monitoring(self._sql)
            monitoring.start()
            self._monitoring_ready = True