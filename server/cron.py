import os
import time
import schedule
from threading import Thread
from crons.coins import Coins 

# https://pypi.org/project/schedule/
class Cron:
    def __init__(self, app, credentials):
        self._app = app
        coins = Coins(app, credentials)
        # Init Crons
        schedule.every().day.at("00:00").do(coins.start)
        # Start crons
        Thread(target=self.__run_schedule).start()

    def __run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)
