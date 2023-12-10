import time
import threading

from deploy_blueprint import deploy_blueprint

class deploy_servers:
    def __init__(self, args, imports, region):
        self._args = args
        self._imports = imports
        self._region = region

    def start(self):
        # Check thread execution status
        current_thread = threading.current_thread()
        if not current_thread.alive:
            return

        # Init shared auxiliary connections
        auxiliary_connections = []

        # Start the Deploy
        try:
            threads = []
            try:
                for server in self._region['sql']:
                    blueprint = deploy_blueprint(self._args, self._imports, self._region)
                    t = threading.Thread(target=blueprint.execute, args=(server,))
                    threads.append(t)
                    t.alive = current_thread.alive
                    t.error = False
                    t.critical = current_thread.critical
                    t.progress = current_thread.progress
                    t.auxiliary = auxiliary_connections
                    t.start()

                # Wait all threads
                while any(t.is_alive() for t in threads):
                    # Check alive
                    if not current_thread.alive:
                        for t in threads:
                            t.alive = False
                    time.sleep(0.5)

                # Ensure all threads are finished
                for t in threads:
                    t.join()

                # Check errors
                current_thread.error = current_thread.error or any(t.error for t in threads)

            except (Exception,KeyboardInterrupt):
                for t in threads:
                    t.alive = False
                for t in threads:
                    t.join()
                raise

        except Exception as e:
            # Stop all threads and store critical error (auxiliary error related)
            current_thread.critical.append(str(e))

        finally:
            # Close existing Auxiliary Connections
            for i in auxiliary_connections:
                i.stop()
