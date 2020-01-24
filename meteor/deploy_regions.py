import os
import time
import threading

from deploy_queries import deploy_queries

class deploy_regions:
    def __init__(self, args, imports, region):
        self._args = args
        self._imports = imports
        self._credentials = imports.credentials
        self._query_template = imports.query_template
        self._region = region

    def start(self):
        # Check thread execution status
        current_thread = threading.current_thread()
        if not current_thread.alive:
            return
        
        environment_type = '[SSH]' if self._region['ssh']['enabled'] else '[LOCAL]'

        # Create Execution Folders
        if not os.path.exists(self._args.execution_path + '/execution/' + self._region['region']):
            os.makedirs(self._args.execution_path + '/execution/' + self._region['region'])

        # Start the Deploy
        deploy = deploy_queries(self._args, self._imports, self._region)

        # Execute 'BEFORE' Queries Once per Region
        if current_thread.alive:
            deploy.execute_before()

        # Start Server Deploy in Parallel
        threads = []
        try:
            for server in self._region['sql']:
                deploy_parallel = deploy_queries(self._args, self._imports, self._region, deploy.query_execution)
                t = threading.Thread(target=deploy_parallel.execute_main, args=(server,))
                threads.append(t)
                t.alive = current_thread.alive
                t.error = False
                t.progress = current_thread.progress
                t.start()

            # Wait all threads
            while any(t.is_alive() for t in threads):
                if not current_thread.alive:
                    for t in threads:
                        t.alive = False
                time.sleep(0.5)

            # Ensure all threads are finished
            for t in threads:
                t.join()

            # Check errors
            current_thread.error = any(t.error for t in threads)

        except (Exception,KeyboardInterrupt):
            for t in threads:
                t.join()
            raise

        # Execute 'AFTER' Queries Once per Region
        if current_thread.alive:
            deploy.execute_after()