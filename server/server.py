from multiprocessing import Process
from multiprocessing.managers import BaseManager

# App Version
version = '1.00-beta.33'

# Init Shared License Class
from license import License
BaseManager.register('License', License)
manager = BaseManager()
manager.start()
l = manager.License(version)

# Init Server Api
from app import App
p = Process(target=App, args=(version,l,))
p.daemon = True
p.start()

# Init Cron
from cron import Cron
Cron(l)
#p2 = Process(target=Cron, args=(l,))
#p2.daemon = True
#p2.start()

# Wait Api
try:
    p.join()
    # p2.join()
except KeyboardInterrupt:
    pass
