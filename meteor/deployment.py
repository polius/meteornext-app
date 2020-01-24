import os
import time
import threading
import signal
from datetime import timedelta

from deploy_regions import deploy_regions

class deployment:
    def __init__(self, args, imports, progress):
        # Init vars
        self._args = args
        self._imports = imports
        self._credentials = imports.credentials
        self._query_template = imports.query_template
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

            try:
                # Init Deploy Progress
                progress = {}
                for region in self._credentials['environments'][self._args.environment]:
                    progress[region['region']] = {}

                # Start Deployment
                threads = []
                for region in self._credentials['environments'][self._args.environment]:
                    deploy_region = deploy_regions(self._args, self._imports, region)
                    t = threading.Thread(target=deploy_region.start)
                    t.alive = True
                    t.error = False
                    t.progress = []
                    t.start()
                    threads.append(t)

                # Track Progress
                t = threading.Thread(target=self.__track_progress, args=(progress, threads, started_datetime, started_time,))
                t.start()
                t.join()

                # Wait all threads
                for t in threads:
                    t.join()

                # Print Execution Finished
                if any(t.error for t in threads):
                    print("- {}Execution Finished. Some queries failed".format('Test ' if self._args.test else ''))
                else:
                    print("- {}Execution Finished Successfully".format('Test ' if self._args.test else ''))

                # Return Execution Status
                return any(t.error for t in threads)

            except KeyboardInterrupt:
                # Supress CTRL+C events
                signal.signal(signal.SIGINT,signal.SIG_IGN)
                print("\n--> Ctrl+C Received. Stopping All Region Processes...")

                # Stop All Threads
                for t in threads:
                    t.alive = False
                
                # Wait All Threads
                for t in threads:
                    t.join()

                print("- {}Execution Interrupted".format('Test ' if self._args.test else ''))   

                # Enable CTRL+C events
                signal.signal(signal.SIGINT, signal.default_int_handler)

                # Raise KeyboardInterrupt
                raise
        finally:
            self._time = time.time()

    def __track_progress(self, progress, threads, started_datetime, started_time):
        current_thread = threading.current_thread()
        current_thread.status = 0

        tracking = True
        while tracking:
            track_progress = True
            # Check if all processes have finished
            if all(not t.is_alive() for t in threads):
                tracking = False

            # Calculate Progress
            for t in threads:
                for r in range(len(t.progress)):
                    item = t.progress.pop(0)

                    if 'e' in item:
                        current_thread.status = 1

                    if item['s'] not in progress[item['r']] or 'e' not in progress[item['r']][item['s']]:
                        progress[item['r']][item['s']] = { "p": item['p'], "d": item['d'], "t": item['t'] }
                    else:
                        progress[item['r']][item['s']]['p'] = item['p']
                        progress[item['r']][item['s']]['d'] = item['d']
                        progress[item['r']][item['s']]['t'] = item['t']

            # Print & Track Progress
            self.__show_execution_header(started_datetime, started_time)

            for region in self._credentials['environments'][self._args.environment]:
                environment_type = '[SSH]  ' if region['ssh']['enabled'] else '[LOCAL]'
                region_total_databases = sum([int(rp['t']) if 't' in rp else 0 for rp in progress[region['region']].values()])
                region_databases = sum([int(rp['d']) if 'd' in rp else 0 for rp in progress[region['region']].values()])
                overall_progress = 0 if region_total_databases == 0 else float(region_databases) / float(region_total_databases) * 100
                print("--> {} Region '{}': {:.2f}% ({}/{} DBs)".format(environment_type, region['region'], overall_progress, region_databases, region_total_databases))

            if track_progress:
                self._progress.track_execution(value=progress)
            time.sleep(1)

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