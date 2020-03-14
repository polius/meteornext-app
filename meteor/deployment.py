import os
import time
import signal
import threading
import traceback
from datetime import timedelta

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

    @property
    def time(self):
        return self._time

    def start(self):
        try:
            # Get Deployment Start Datetime
            started_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            started_time = time.time()

            # Show Header
            self.__show_execution_header(started_datetime, started_time)

            # Create Execution Folder
            if not os.path.exists("{}/execution".format(self._args.path)):
                os.makedirs("{}/execution".format(self._args.path))

            # Init Progress dictionary
            progress = {i['name']: {} for i in self._config['regions']}

            # Start Deployment
            threads = []
            for region in self._config['regions']:
                r = Region(self._args, region)
                t = threading.Thread(target=r.deploy)
                threads.append(t)
                t.start()

            while any(t.is_alive() for t in threads):
                self.__track_overall(progress, started_datetime, started_time)
                time.sleep(1)

            # Print Execution Finished
            queries_failed = False
            for i in progress.values():
                for j in i.values():
                    if j['e']:
                        queries_failed = True
    
            # Print status
            if queries_failed:
                print("- {}Execution Finished. Some queries failed".format('Test ' if self._args.test else ''))
            else:
                print("- {}Execution Finished Successfully".format('Test ' if self._args.test else ''))

            # Return status
            return 1 if queries_failed else 0

        except KeyboardInterrupt:
            # Supress CTRL+C events
            signal.signal(signal.SIGINT,signal.SIG_IGN)
            print("--> Ctrl+C Received. Interrupting all regions...")

            # Interrupt Deployments
            int_threads = []
            for region in self._config['regions']:
                r = Region(self._args, region)
                t = threading.Thread(target=r.sigint())
                int_threads.append(t)
                t.start()
            for t in int_threads:
                t.join()

            # Wait all deployments to be interrupted
            for t in threads:
                t.join()

            print("--> {}Execution Interrupted Successfully".format('Test ' if self._args.test else ''))   

            # Enable CTRL+C events
            signal.signal(signal.SIGINT, signal.default_int_handler)

            # Raise KeyboardInterrupt
            raise

        finally:
            self._time = time.time()

    def __track_overall(self, progress, started_datetime, started_time):
        # Start tracking all regions
        threads = []
        for region in self._imports.config['regions']:
            # Get progress
            r = Region(self._args, region)
            t = threading.Thread(target=r.get_progress)
            t.region = region['name']
            t.progress = {}
            threads.append(t)
            t.start()

        # Wait tracking to finish in all regions
        for t in threads:
            t.join()
            if len(t.progress.keys()) > 0:
                progress[t.region] = t.progress

        # Compute progress
        self.__show_execution_header(started_datetime, started_time)
        for region in self._imports.config['regions']:
            environment_type = '[SSH]  ' if region['ssh']['enabled'] else '[LOCAL]'
            region_total_databases = sum([int(rp['t']) if 't' in rp else 0 for rp in progress[region['name']].values()])
            region_databases = sum([int(rp['d']) if 'd' in rp else 0 for rp in progress[region['name']].values()])
            overall_progress = 0 if region_total_databases == 0 else float(region_databases) / float(region_total_databases) * 100
            print("--> {} Region '{}': {:.2f}% ({}/{} DBs)".format(environment_type, region['name'], overall_progress, region_databases, region_total_databases))
            self._progress.track_execution(value=progress)

    def __show_execution_header(self, started_datetime, started_time):
        # Clean Console
        os.system('cls' if os.name == 'nt' else 'clear')
        # Show Header
        title = "|  TEST EXECUTION                                                  |" if self._args.test else "|  DEPLOYMENT                                                      |"
        print("+==================================================================+")
        print(title)
        print("+==================================================================+")
        # Show Execution Status
        elapsed = str(timedelta(seconds=time.time() - started_time))
        print("> Started: {} > Elapsed: {}".format(started_datetime, elapsed))

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