import os
import imp

class Coins:
    def __init__(self, app, credentials):
        self._app = app
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)

    def start(self):
        if not self._app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            print("[CRON] Giving coins...")
            query = """
                UPDATE users u
                JOIN groups g ON g.id = u.group_id
                SET u.coins = IF (u.coins + g.coins_day > coins_max, coins_max, u.coins + g.coins_day);
            """
            self._mysql.execute(query)