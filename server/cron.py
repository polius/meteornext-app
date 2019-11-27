import json
import time
import shutil
import schedule
import threading

class Cron:
    def __init__(self, sql):
        print("[CRON] Starting...")
        self._sql = sql
        # Init Crons
        schedule.every().day.at("00:00").do(self.__coins)
        schedule.every().day.at("00:00").do(self.__logs)
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
        self._sql.execute(query)

    def __logs(self):
        print("[CRON] Cleaning logs...")
        # Get expiration value
        setting = self._sql.execute("SELECT value FROM settings WHERE name = 'LOGS'")

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
