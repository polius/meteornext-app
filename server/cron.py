import os
import json
import time
import shutil
import schedule
import threading

import models.mysql

# https://pypi.org/project/schedule/
class Cron:
    def __init__(self, credentials):
        print("[CRON] Starting...")
        self._mysql = models.mysql.mysql(credentials)
        # Init Crons
        schedule.every().day.at("00:00").do(self.__coins)
        schedule.every().day.at("00:00").do(self.__logs, credentials['path'])
        # schedule.every().minute.at(":20").do(self.__logs, credentials['path'])

        # Start Cron Listener
        t = threading.Thread(target=self.__run_schedule)
        t.daemon = True
        t.start()

    def __run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __coins(self):
        print("[CRON] Giving coins...")
        query = """
            UPDATE users u
            JOIN groups g ON g.id = u.group_id
            SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
        """
        self._mysql.execute(query)

    def __logs(self, path):
        print("[CRON] Cleaning logs...")
        # Get expiration value
        setting = self._mysql.execute("SELECT value FROM settings WHERE name = 'LOGS'")

        # Check expiration is active
        if len(setting) > 0:
            setting = json.loads(setting[0]['value'])
            if 'expire' in setting['local']:
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
                """.format(int(setting['local']['expire']))
                expired = self._mysql.execute(query)

                # Expire deployments
                for i in expired:
                    # DISK
                    shutil.rmtree('{}/logs/{}'.format(path, i['uri']), ignore_errors=True)
                    # SQL
                    self._mysql.execute("UPDATE deployments_{} SET expired = 1 WHERE id = {}".format(i['mode'], i['id']))
