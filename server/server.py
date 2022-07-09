from multiprocessing import Process
from multiprocessing.managers import BaseManager

# App Version
version = '1.00-beta.34'
sentry_dsn = 'https://7de474b9a31148d29d10eb5aea1dff71@o1100742.sentry.io/6138582'

# Init Shared License Class
from license import License
BaseManager.register('License', License)
manager = BaseManager()
manager.start()
l = manager.License(version)

# Init Server Api
from app import App
p = Process(target=App, args=(version,l,sentry_dsn,))
p.start()

# Init Cron
from cron import Cron
p2 = Process(target=Cron, args=(l,sentry_dsn,))
p2.start()

# Wait Api
try:
    p.join()
    p2.join()
except KeyboardInterrupt:
    pass
