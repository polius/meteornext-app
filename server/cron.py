import os
import json
import uuid
import time
import hashlib
import shutil
import requests
import schedule
import threading

import routes.deployments.deployments
import routes.deployments.views.basic
import routes.deployments.views.pro
import routes.deployments.views.inbenta

class Cron:
    def __init__(self, app, license, license_conf, blueprints, sql):
        self._app = app
        self._license = license
        self._license_conf = license_conf
        self._blueprints = blueprints
        self._sql = sql

    @property
    def license(self):
        return self._license

    def KMMLeSdKHFP9hBQCm7Pg9J3VtvjsNeEnuc4nyDV9ZD7QDxQUwaRgyddSZqxhsFP3(self):
        return 'FBfLXedVRQ4Kj4tAZ2EUcYruu8KX8WPYLaxjaCYzxuM3yF89aPXwLxE2AMwWz5Jr'

    def start(self):
        # Init Crons
        schedule.every(1).minutes.do(self.__license, 'minute')
        schedule.every(30).seconds.do(self.__executions)
        schedule.every().day.at("00:00").do(self.__license, 'day')
        schedule.every().day.at("00:00").do(self.__coins)
        schedule.every().day.at("00:00").do(self.__logs)

        # Start Cron Listener
        t = threading.Thread(target=self.__run_schedule)
        t.daemon = True
        t.start()

    def __run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __license(self, mode):
        if mode == 'minute' and self._license['status']:
            return
        if mode == 'hour' and not self._license['status']:
            return
        try:
            # Generate trial
            self._license_conf['trial'] = str(uuid.uuid4())

            # Check license
            response = requests.post("http://34.252.139.218:12350/license", json=self._license_conf, allow_redirects=False)
            response_code = response.status_code
            response_status = response.status_code == 200
            response_text = json.loads(response.text)['response']

            # Solve trial
            if response_status == 200:
                response_trial = json.loads(response.text)['trial']
                trial = ','.join([str(ord(i)) for i in self._license_conf['trial']])
                trial = hashlib.sha3_256(trial.encode()).hexdigest()

                # Validate keys
                if response_trial != trial:
                    response_text = "The license is not valid"
                    response_code = 401
                    response_status = False

        except requests.exceptions.RequestException as e:
            response_text = "A connection with the licensing server could not be established"
            response_code = 404
            response_status = False    
        finally:
            self._license = {'status': response_status, 'code': response_code, 'response': response_text}
            for b in self._blueprints:
                b.license(self._license)

    def __executions(self):
        # Basic Deployments
        basic = routes.deployments.views.basic.Basic(self._app, self._sql)
        basic.check_finished()
        basic.check_scheduled()

        # Pro Deployments
        pro = routes.deployments.views.pro.Pro(self._app, self._sql)
        pro.check_finished()
        pro.check_scheduled()

        # Inbenta Deployments
        inbenta = routes.deployments.views.inbenta.Inbenta(self._app, self._sql)
        inbenta.check_finished()
        inbenta.check_scheduled()

        # Deployments
        deployments = routes.deployments.deployments.Deployments(self._app, self._sql)
        deployments.check_queued()

    def __coins(self):
        if not self._license['status']:
            return

        print("- Giving coins...")
        query = """
            UPDATE users u
            JOIN groups g ON g.id = u.group_id
            SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
        """
        self._sql.execute(query)

    def __logs(self):
        if not self._license['status']:
            return

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
                    UNION ALL
                    SELECT id, uri, 'inbenta' AS 'mode'
                    FROM deployments_inbenta
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
