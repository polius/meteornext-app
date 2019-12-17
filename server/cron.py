import os
import json
import time
import shutil
import requests
import schedule
import threading

class Cron:
    def __init__(self, sql, license):
        self._sql = sql
        self._license = license

    def KMMLeSdKHFP9hBQCm7Pg9J3VtvjsNeEnuc4nyDV9ZD7QDxQUwaRgyddSZqxhsFP3(self):
        return 'FBfLXedVRQ4Kj4tAZ2EUcYruu8KX8WPYLaxjaCYzxuM3yF89aPXwLxE2AMwWz5Jr'

    def start(self):
        # Check License
        self.__license()

        # Init Crons
        schedule.every().day.at("00:00").do(self.__license)
        schedule.every().day.at("00:00").do(self.__coins)
        schedule.every().day.at("00:00").do(self.__logs)
        schedule.every(1).minutes.do(self.__license)

        # Start Cron Listener
        t = threading.Thread(target=self.__run_schedule)
        t.daemon = True
        t.start()

    def __run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __license(self):
        print("LICENSE")
        retries = 10
        for i in range(retries+1):
            if i == retries:
                os._exit(0)
            try:
                response = requests.post("http://www.poliuscorp.com:12350/license", json=self._license)
                response_text = json.loads(response.text)['response']
                check_license = False

                if response.status_code != 200:
                    print('- ' + response_text)
                    os._exit(0)
                break

            except requests.exceptions.RequestException as e:
                print("- [Attempt {}/{}] A connection with the licensing server could not be established. Trying again in 5 seconds...".format(i+1, retries))
                time.sleep(5)

    def __coins(self):
        print("- Giving coins...")
        query = """
            UPDATE users u
            JOIN groups g ON g.id = u.group_id
            SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
        """
        self._sql.execute(query)

    def __logs(self):
        print("- Cleaning logs...")
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
