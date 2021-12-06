import os
import json
import time
import signal
import threading

from region import Region
from deploy_servers import deploy_servers

class deploy_regions:
    def __init__(self, args, imports, region):
        self._args = args
        self._imports = imports
        self._region = region
        # Init Region Class
        self._Region = Region(args, region)

    def start(self):
        try:
            # Create Execution Folder
            path = f"{self._args.path}/execution/{self._region['name']}_{self._region['id']}"
            if not os.path.exists(path):
                os.makedirs(path)

            # Start Deployment
            deploy_server = deploy_servers(self._args, self._imports, self._region)
            deploy = threading.Thread(target=deploy_server.start)
            deploy.alive = True
            deploy.error = False
            deploy.critical = []
            deploy.progress = []
            deploy.start()

            # Track Progress
            track = threading.Thread(target=self.__track_progress, args=(deploy,))
            track.start()
            track.join()

            # Wait all threads
            deploy.join()

        except KeyboardInterrupt:
            # Supress CTRL+C events
            signal.signal(signal.SIGINT,signal.SIG_IGN)

            # Stop Execution Threads
            deploy.alive = False

            # Wait Execution Threads
            deploy.join()

            # Enable CTRL+C events
            signal.signal(signal.SIGINT, signal.default_int_handler)

    def __track_progress(self, deploy):
        progress = {"progress": {}}
        tracking = True
        while tracking:
            # Check if all processes have finished
            if not deploy.is_alive():
                tracking = False

            # Calculate Progress
            for r in range(len(deploy.progress)):
                item = deploy.progress.pop(0)
                progress['progress'][item['s']] = { "p": item['p'], "d": item['d'], "t": item['t'], "e": deploy.error }

            # Get Errors
            if len(deploy.critical) > 0:
                progress['errors'] = deploy.critical

            # Write Progress
            with open(f"{self._args.path}/execution/{self._region['name']}_{self._region['id']}/progress.json", 'w') as outfile:
                json.dump(progress, outfile, default=self.__dtSerializer, separators=(',', ':'))

            # Sleep for 1 second
            time.sleep(1)

    # Parse JSON objects
    def __dtSerializer(self, obj):
        return obj.__str__()