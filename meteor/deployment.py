import os
import time
import signal
import threading

from deploy_regions import deploy_regions
from region import Region

class deployment:
    def __init__(self, args, imports, progress):
        # Init vars
        self._args = args
        self._imports = imports
        self._config = imports.config
        self._progress = progress
        self._time = None
        self._sigterm = False
        self._threads = []

    @property
    def time(self):
        return self._time

    def start(self):
        try:
            # Handle SIGTERM
            signal.signal(signal.SIGTERM, self.__sigterm)

            # Get Deployment Start Datetime
            started_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            started_time = time.time()

            # Create Execution Folder
            if not os.path.exists(f"{self._args.path}/execution"):
                os.makedirs(f"{self._args.path}/execution")

            # Create Deployments Folder
            if not os.path.exists(f"{self._args.path}/deployments"):
                os.makedirs(f"{self._args.path}/deployments")

            # Init Progress dictionary
            progress = {i['name']: {} for i in self._config['regions']}

            # Start Deployment
            for region in self._config['regions']:
                r = Region(self._args, region)
                t = threading.Thread(target=r.deploy)
                self._threads.append(t)
                t.start()

            while any(t.is_alive() for t in self._threads):
                # Track Overall Progress
                self.__track_overall(progress, started_datetime, started_time)
                # Check Sigterm
                if self._sigterm:
                    raise KeyboardInterrupt()
                time.sleep(1)

            # Track again Overall Progress 
            self.__track_overall(progress, started_datetime, started_time)

            # Check Critical Errors
            errors = []
            for region in self._config['regions']:
                if 'errors' in progress[region['name']]:
                    for i in progress[region['name']]['errors']:
                        if i not in errors:
                            errors.append(i)
            if len(errors) > 0:
                errors_parsed = ''
                for i in errors:
                    errors_parsed += i + '\n'
                errors_parsed = errors_parsed[:-1]
                raise Exception(errors_parsed)

            # Print Execution Finished
            queries_failed = False
            for i in progress.values():
                for j in i['progress'].values():
                    if j['e']:
                        queries_failed = True

            # Return status
            return 1 if queries_failed else 0

        except KeyboardInterrupt:
            signal.signal(signal.SIGINT,signal.SIG_IGN)
            if self._sigterm:
                self.__terminate_deployment()
            else:
                self.__interrupt_deployment()
            signal.signal(signal.SIGINT, signal.default_int_handler)
            raise
        finally:
            self._time = time.time()

    def __sigterm(self, signum, frame):
        self._sigterm = True

    def __interrupt_deployment(self):
        threads = []
        for region in self._config['regions']:
            r = Region(self._args, region)
            t = threading.Thread(target=r.sigint())
            t.daemon = True
            threads.append(t)
            t.start()
        while any(t.is_alive() for t in self._threads):
            if self._sigterm:
                self.__terminate_deployment()
                break
            time.sleep(1)

    def __terminate_deployment(self):
        threads = []
        for region in self._config['regions']:
            r = Region(self._args, region)
            t = threading.Thread(target=r.sigkill())
            threads.append(t)
            t.start()
        for t in self._threads:
            t.join()

    def __track_overall(self, progress, started_datetime, started_time):
        # Start tracking all regions
        threads = []
        for region in self._imports.config['regions']:
            # Get progress
            r = Region(self._args, region)
            t = threading.Thread(target=r.get_progress)
            t.daemon = True
            t.region = region['name']
            t.progress = {}
            threads.append(t)
            t.start()

        # Wait tracking to finish in all regions
        for t in threads:
            t.join()
            if len(t.progress.keys()) > 0:
                progress[t.region] = t.progress

        # Track execution process
        track = {}
        for k, v in progress.items():
            track[k] = v['progress'] if 'progress' in v else {}
        self._progress.track_execution(value=track)

    ##########
    # REMOTE #
    ##########
    def deploy(self):
        region = [i for i in self._config['regions'] if i['name'] == self._args.region]
        if len(region) > 0:
            deploy_region = deploy_regions(self._args, self._imports, region[0])
            deploy_region.start()

    def compress(self):
        region = [i for i in self._config['regions'] if i['name'] == self._args.region]
        if len(region) > 0:
            r = Region(self._args, region[0])
            r.compress_logs()