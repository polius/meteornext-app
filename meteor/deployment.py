import os
import time
import signal
import threading
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

            # Show Header
            self.__show_execution_header(started_datetime, started_time)

            # Create Execution Folder
            if not os.path.exists("{}/execution".format(self._args.path)):
                os.makedirs("{}/execution".format(self._args.path))

            # Create Logs Folder
            if not os.path.exists("{}/logs".format(self._args.path)):
                os.makedirs("{}/logs".format(self._args.path))

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
            if self._sigterm:
                self.__terminate_deployment()
            else:
                self.__interrupt_deployment()
            # Enable CTRL+C events
            signal.signal(signal.SIGINT, signal.default_int_handler)
            # Raise KeyboardInterrupt
            raise
        finally:
            self._time = time.time()

    def __sigterm(self, signum, frame):
        self._sigterm = True

    def __interrupt_deployment(self):
        print("--> SIGINT Received. Interrupting all regions...")
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
        print("--> {}Execution Interrupted Successfully".format('Test ' if self._args.test else ''))

    def __terminate_deployment(self):
        print("--> SIGTERM Received. Terminating all regions...")
        threads = []
        for region in self._config['regions']:
            r = Region(self._args, region)
            t = threading.Thread(target=r.sigkill())
            threads.append(t)
            t.start()
        for t in self._threads:
            t.join()
        print("--> {}Execution Terminated Successfully".format('Test ' if self._args.test else ''))   

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
        errors = []
        for t in threads:
            t.join()
            if len(t.progress.keys()) > 0:
                progress[t.region] = t.progress

        # Compute progress
        self.__show_execution_header(started_datetime, started_time)
        for region in self._imports.config['regions']:
            if region['name'] in progress.keys() and 'progress' in progress[region['name']]:
                environment_type = '[SSH]  ' if region['ssh']['enabled'] else '[LOCAL]'
                region_total_databases = sum([int(rp['t']) if 't' in rp else 0 for rp in progress[region['name']]['progress'].values()])
                region_databases = sum([int(rp['d']) if 'd' in rp else 0 for rp in progress[region['name']]['progress'].values()])
                overall_progress = 0 if region_total_databases == 0 else float(region_databases) / float(region_total_databases) * 100
                print("--> {} Region '{}': {:.2f}% ({}/{} DBs)".format(environment_type, region['name'], overall_progress, region_databases, region_total_databases))

        # Track execution process
        track = {}
        for k, v in progress.items():
            track[k] = v['progress'] if 'progress' in v else {}
        self._progress.track_execution(value=track)

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