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

            # Create Execution Folder
            if not os.path.exists(f"{self._args.path}/execution"):
                os.makedirs(f"{self._args.path}/execution")

            # Init Progress
            progress = [{"id": i['id'], "name": i['name'], "shared": i['shared'], "servers": []} for i in self._config['regions']]
            # Start Deployment
            for region in self._config['regions']:
                r = Region(self._args, region)
                t = threading.Thread(target=r.deploy)
                self._threads.append(t)
                t.start()

            while any(t.is_alive() for t in self._threads):
                # Track Overall Progress
                self.__track_overall(progress)
                # Check Sigterm
                if self._sigterm:
                    raise KeyboardInterrupt()
                time.sleep(1)

            # Track again Overall Progress 
            self.__track_overall(progress)

            # Check Critical Errors
            errors = []
            for region in progress:
                if 'errors' in region:
                    for error in region['errors']:
                        if error not in errors:
                            errors.append(error)

            if len(errors) > 0:
                errors_parsed = ''
                for i in errors:
                    errors_parsed += i + '\n'
                errors_parsed = errors_parsed[:-1]
                raise Exception(errors_parsed)

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

    def __track_overall(self, progress):
        # Start tracking all regions
        threads = []
        for region in self._imports.config['regions']:
            # Get progress
            r = Region(self._args, region)
            t = threading.Thread(target=r.get_progress)
            t.daemon = True
            t.region = region
            t.progress = {}
            threads.append(t)
            t.start()

        # Wait tracking to finish in all regions
        for t in threads:
            t.join()
            index = next((i for i, x in enumerate(progress) if x["id"] == t.region['id']), None)
            if 'execution' in t.progress:
                progress[index]['servers'] = t.progress['execution']
            if 'errors' in t.progress:
                progress[index]['errors'] = t.progress['errors']
        self._progress.track_execution(value=progress)

    ##########
    # REMOTE #
    ##########
    def deploy(self):
        region = [i for i in self._config['regions'] if i['id'] == int(self._args.region)]
        if len(region) > 0:
            deploy_region = deploy_regions(self._args, self._imports, region[0])
            deploy_region.start()

    def compress(self):
        region = [i for i in self._config['regions'] if i['id'] == int(self._args.region)]
        if len(region) > 0:
            r = Region(self._args, region[0])
            r.compress_logs()