import os
import sys
import time
import signal
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
        try:
            self._start_time = time.time()
            self.__validate_regions()
        finally:
            self._time = time.time()

    def __validate_regions(self):
        try:
            # Init validation
            progress = []
            for region in self._config['regions']:
                progress.append({'id': region['id'], 'name': region['name'], 'shared': region['shared']})
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
                validate_region = validate_regions(self._args, region, self._progress)
                t = threading.Thread(target=validate_region.validate)
                t.progress = {'id': region['id']}
                t.daemon = True
                t.alive = True
                threads.append(t)
                t.start()

            # Track Progress
            while any(t.is_alive() for t in threads):
                error = self.__track_regions(threads, progress)
                time.sleep(1)
            error = self.__track_regions(threads, progress)

            # Check validation errors
            if error:
                raise Exception("- Regions Not Passed the Environment Validation")

        except KeyboardInterrupt:
            signal.signal(signal.SIGINT,signal.SIG_IGN)
            signal.signal(signal.SIGTERM,signal.SIG_IGN)
            for t in threads:
                t.alive = False
            for t in threads:
                t.join()
            error = self.__track_regions(threads, progress)
            if error:
                raise KeyboardInterrupt("- Regions Not Passed the Environment Validation")
            raise

    def __track_regions(self, threads, progress):
        error = False
        for t in threads:
            # Build progress dictionary
            index = next((i for i, x in enumerate(progress) if x["id"] == t.progress['id']), None)
            if 'success' in t.progress:
                progress[index]['success'] = t.progress['success']
            # Check SSH error
            if 'error' in t.progress:
                error = True
                progress[index]['error'] = t.progress['error']
            # Check SQL errors
            if 'errors' in t.progress:
                error = True
                progress[index]['errors'] = t.progress['errors']

        self._progress.track_validation(progress)
        return error
