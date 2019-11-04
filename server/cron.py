import os
import imp
import time
import schedule
from threading import Thread

# https://pypi.org/project/schedule/
class Cron:
    def __init__(self, app, credentials):
        self._app = app
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)
        # Init Crons
        schedule.every().day.at("00:00").do(self.__coins)
        # Start crons
        Thread(target=self.__run_schedule).start()

    def __run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __coins(self):
        if not self._app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            print("[CRON] Giving coins...")
            query = """
                UPDATE users u
                JOIN groups g ON g.id = u.group_id
                SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
            """
            self._mysql.execute(query)
