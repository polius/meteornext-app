import os
import re
import sys
import time
import threading
import hashlib

from validate_regions import validate_regions

class validation:
    def __init__(self, args, imports, progress):
        # Init vars
        self._args = args
        self._config = imports.config
        self._progress = progress
        self._time = None

    @property
    def time(self):
        return self._time

    def start(self):
        print("+==================================================================+")
        print("|  VALIDATION                                                      |")
        print("+==================================================================+")
        try:
            self._start_time = time.time()
            self.__validate_regions()
        finally:
            self._time = time.time()

    def __validate_regions(self):
        try:
            # Init validation
            progress = {}
            for region in self._config['regions']:
                progress[region['name']] = {}
            self._progress.track_validation(progress)

            # Generate App Version
            if not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')):
                local_path = os.path.dirname(os.path.realpath(__file__))
                version = ''
                files = os.listdir(local_path)
                for f in files:
                    if not os.path.isdir("{}/{}".format(local_path, f)) and not f.endswith('.pyc') and not f.startswith('.') and not f.endswith('.gz') and f not in ['version.txt', 'blueprint.py', 'config.json']:
                        with open("{}/{}".format(local_path, f), 'rb') as file_content:
                            file_hash = hashlib.sha512(file_content.read()).hexdigest()
                            version += file_hash
                with open('{}/version.txt'.format(local_path), 'w') as file_content:
                    file_content.write(version)

            # Start validation
            threads = []
            for region in self._config['regions']:
                validate_region = validate_regions(self._args, region)
                t = threading.Thread(target=validate_region.validate)
                t.progress = {}
                threads.append(t)
                t.start()

            # Wait all threads
            for t in threads:
                t.join()

            # Track Progress
            tracking = True
            error = False

            for t in threads:
                # Build progress dictionary
                progress[t.progress['region']] = { "success": t.progress['success'] }
                # Check SSH error
                if 'error' in t.progress:
                    error = True
                    progress[t.progress['region']]['error'] = t.progress['error']
                # Check SQL errors
                if 'errors' in t.progress:
                    error = True
                    progress[t.progress['region']]['errors'] = t.progress['errors']

            self._progress.track_validation(progress)

            # Check validation errors
            if error:
                error_msg = "- Regions Not Passed the Environment Validation."
                self._progress.error(error_msg[2:])
                raise Exception(error_msg)
            
            print("- Regions Validation Passed!")

        except KeyboardInterrupt:
            print("\n--> Ctrl+C received. Stopping the execution...")
            for t in threads:
                t.join()
            raise