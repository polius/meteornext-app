import os
import sys
import json
import time
import shutil
import signal
import paramiko
import threading
import subprocess

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
            if not os.path.exists("{}/execution/{}".format(self._args.path, self._args.region)):
                os.makedirs("{}/execution/{}".format(self._args.path, self._args.region))

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
            track.alive = True
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
        current_thread = threading.current_thread()
        tracking = True
        while tracking:
            track_progress = True

            # Check current thread status
            if not current_thread.alive:
                return

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
            with open("{}/execution/{}/progress.json".format(self._args.path, self._region['name']), 'w') as outfile:
                json.dump(progress, outfile, default=self.__dtSerializer, separators=(',', ':'))

            # Sleep for 1 second
            time.sleep(1)

    # Parse JSON objects
    def __dtSerializer(self, obj):
        return obj.__str__()