import os
import imp
import time
import schedule
import threading

# https://pypi.org/project/schedule/
class Cron:
    def __init__(self, app, credentials):
        print("[CRON] Starting...")
        self._app = app
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)
        # Init Crons
        schedule.every().day.at("00:00").do(self.__coins)
        # Start Cron Listener
        threading.Thread(target=self.__run_schedule).start()

    def __run_schedule(self):
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            pass

    def __coins(self):
        print("[CRON] Giving coins...")
        query = """
            UPDATE users u
            JOIN groups g ON g.id = u.group_id
            SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
        """
        self._mysql.execute(query)
