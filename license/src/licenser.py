# curl -d "{\"email\":\"poliuscorp\",\"key\":\"KeyXc4et9qksf3ajMjItPpQyvCBWwYwO7fRT6xBnrAY=\",\"uuid\":\"3037522049778\",\"challenge\":\"123\"}" -H "Content-Type:application/json" https://license.meteor2.io/
from gunicorn.app.base import Application, Config
import json
import gunicorn
from gunicorn import glogging
from gunicorn.workers import sync
from app import app

class GUnicornFlaskApplication(Application):
    def __init__(self, app):
        self.usage, self.callable, self.prog, self.app = None, None, None, app

    def run(self, **options):
        self.cfg = Config()
        [self.cfg.set(key, value) for key, value in options.items()]
        return Application.run(self)

    load = lambda self:self.app

if __name__ == "__main__":
    # Init Gunicorn App
    gunicorn_app = GUnicornFlaskApplication(app)
    gunicorn_app.run(worker_class="gunicorn.workers.sync.SyncWorker", bind='unix:/root/licenser/licenser.sock', capture_output=True, errorlog='error.log', daemon=True)