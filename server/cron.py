import os
import sys
import json
import time
import schedule
import threading
import traceback

import routes.deployments.deployments
import routes.deployments.views.basic
import routes.deployments.views.pro
import apps.monitoring.monitoring

class Cron:
    def __init__(self, app, license, blueprints, sql):
        self._app = app
        self._license = license
        self._sql = sql

        @app.before_first_request
        def start():
            # One-Time Tasks
            self.__one_time()
            # Schedule Tasks
            schedule.every(10).seconds.do(self.__run_threaded, self.__executions)
            schedule.every().day.at("00:00").do(self.__run_threaded, self.__coins)
            schedule.every().day.at("00:00").do(self.__run_threaded, self.__logs)
            schedule.every().day.at("00:00").do(self.__run_threaded, self.__monitoring_clean)
            schedule.every().hour.do(self.__run_threaded, self.__client_clean)

            # Start Cron Listener
            t = threading.Thread(target=self.__run_schedule)
            t.start()

    def __one_time(self):
        # Clean "regions_update" table
        self._sql.execute("TRUNCATE TABLE regions_update")

    def __run_threaded(self, job_func):
        job_thread = threading.Thread(target=job_func)
        job_thread.start()

    def __run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __executions(self):
        try:
            # Basic Deployments
            basic = routes.deployments.views.basic.Basic(self._app, self._sql, self._license)
            basic.check_finished()
            basic.check_scheduled()

            # Pro Deployments
            pro = routes.deployments.views.pro.Pro(self._app, self._sql, self._license)
            pro.check_finished()
            pro.check_scheduled()

            # Deployments
            deployments = routes.deployments.deployments.Deployments(self._app, self._sql, self._license)
            deployments.check_queued()
        except Exception:
            traceback.print_exc()

    def __coins(self):
        try:
            if not self._license.validated:
                return
            query = """
                UPDATE users u
                JOIN groups g ON g.id = u.group_id
                SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
            """
            self._sql.execute(query)
        except Exception:
            traceback.print_exc()

    def __logs(self):
        try:
            if not self._license.validated:
                return
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
        except Exception:
            traceback.print_exc()

    def __monitoring_clean(self):
        try:
            monitoring = apps.monitoring.monitoring.Monitoring(self._sql)
            monitoring.clean()
        except Exception:
            traceback.print_exc()

    def __client_clean(self):
        try:
            query = """
                DELETE cq
                FROM client_queries cq
                JOIN users u ON u.id = cq.user_id
                JOIN groups g ON g.id = u.group_id
                WHERE DATE_ADD(DATE(cq.date), INTERVAL g.client_tracking_retention DAY) <= CURRENT_DATE
            """
            self._sql.execute(query)
        except Exception:
            traceback.print_exc()
