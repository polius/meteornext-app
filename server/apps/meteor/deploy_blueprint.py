import os
import re
import json
import time
import shutil
import inspect
import threading
import importlib.util

from connector import connector
from deploy_queries import deploy_queries

class deploy_blueprint:
    def __init__(self, args, imports, region):
        self._args = args
        self._imports = imports
        self._region = region
        self._blueprint = importlib.util.spec_from_file_location("blueprint", "{}/blueprint.py".format(self._args.path)).loader.load_module().blueprint()
        # Store Threading Shared Vars 
        self._databases = []
        self._progress = []

    @property
    def blueprint(self):
        return self._blueprint

    def execute(self, server):
        # Create Execution Server Folder (if exists, then recreate)
        execution_server_folder = f"{self._args.path}/execution/{self._region['id']}/{server['id']}/"
        if os.path.exists(execution_server_folder):
            shutil.rmtree(execution_server_folder)
        os.mkdir(execution_server_folder)

        # Execute before
        self.__before(server)

        # Execute main
        self.__main(server)

        # Execute after
        self.__after(server)

    def __before(self, server):
        # Get the current thread
        current_thread = threading.current_thread()
        if not current_thread.alive:
            return

        # Start Deploy
        try:
            query_instance = deploy_queries(self._args, self._imports, self._region, server, 'before', 'b')
            query_instance.start_sql_connection()

            # Execute Before
            self._blueprint.before(query_instance, self._imports.config['params']['environment'], self._region['name'], server['name'])

        except Exception as e:
            # Build error message
            inner_frames = inspect.getinnerframes(e.__traceback__)
            found = False
            for frame in reversed(inner_frames):
                if any(frame.filename.endswith(i) for i in ['blueprint.py','blueprint.pyc']):
                    found = True
                    current_thread.critical.append("{}: {} (line {})".format(type(e).__name__, str(e).capitalize(), frame.lineno))
                    break
            if not found:
                current_thread.critical.append("{}: {}".format(type(e).__name__, str(e).capitalize()))
        finally:
            query_instance.close_sql_connection()

    def __main(self, server):
        # Check thread execution status
        current_thread = threading.current_thread()
        if len(current_thread.critical) > 0 or not current_thread.alive:
            return

        # Get all server databases
        conn_data = {"sql": server}
        conn = connector(conn_data)
        conn.start()
        databases = conn.get_all_databases()
        self._databases = [i for i in databases]
        conn.stop()

        # Deployment in Parallel
        try:
            threads = []
            for i in range(int(self._imports.config['params']['threads'])):
                t = threading.Thread(target=self.__execute_main_databases, args=(server,i+1,))
                t.alive = current_thread.alive
                t.error = False
                t.critical = []
                t.auxiliary = current_thread.auxiliary
                t.start()
                threads.append(t)

            # Track progress
            while any(t.is_alive() for t in threads):
                # Check alive
                if not current_thread.alive:
                    for t in threads:
                        t.alive = False
                # Track progress
                self.__track_execution_progress(server, databases)
                time.sleep(1)

            # Check progress again
            self.__track_execution_progress(server, databases)

            # Check critical errors
            for t in threads:
                if len(t.critical) > 0:
                    for i in t.critical:
                        if i not in current_thread.critical:
                            current_thread.critical.append(json.dumps(i)[1:-1])

            # Check errors
            current_thread.error = current_thread.error or any(t.error for t in threads)

        except (Exception, KeyboardInterrupt):
            for t in threads:
                t.alive = False
            for t in threads:
                t.join()
            raise

    def __after(self, server):
        # Get the current thread
        current_thread = threading.current_thread()
        if len(current_thread.critical) > 0 or not current_thread.alive:
            return

        # Start Deploy
        try:
            query_instance = deploy_queries(self._args, self._imports, self._region, server, 'after', 'a')
            query_instance.start_sql_connection()

            # Execute After
            self._blueprint.after(query_instance, self._imports.config['params']['environment'], self._region['name'], server['name'])

        except Exception as e:
            # Build error message
            inner_frames = inspect.getinnerframes(e.__traceback__)
            found = False
            for frame in reversed(inner_frames):
                if any(frame.filename.endswith(i) for i in ['blueprint.py','blueprint.pyc']):
                    found = True
                    current_thread.critical.append("{}: {} (line {})".format(type(e).__name__, str(e).capitalize(), frame.lineno))
                    break
            if not found:
                current_thread.critical.append("{}: {}".format(type(e).__name__, str(e).capitalize()))
        finally:
            query_instance.close_sql_connection()

    def __track_execution_progress(self, server, databases):
        current_thread = threading.current_thread()
        d = len(self._progress)
        progress = float(d)/float(len(databases)) * 100
        item = {"id": server['id'], "name": server['name'], "shared": server['shared'], "p": float('%.2f' % progress), "d": d, "t": len(databases)}
        current_thread.progress.append(item)

    def __execute_main_databases(self, server, i):
        current_thread = threading.current_thread()

        # Set SQL Connection
        query_instance = deploy_queries(self._args, self._imports, self._region, server, 'main', i)
        query_instance.start_sql_connection()

        while len(self._databases) > 0:
            try:
                # Detect Thread KeyboardInterrupt
                if not current_thread.alive:
                    break

                # Pick the next database to perform the execution
                try:
                    database = self._databases.pop(0)
                    query_instance.database = database
                except IndexError:
                    break

                # Perform the execution to the Database
                self._blueprint.main(query_instance, self._imports.config['params']['environment'], self._region['name'], server['name'], database)

            except Exception as e:
                # Build error message
                if e.__class__.__name__ == 'InterfaceError':
                    current_thread.critical.append("Lost connection to MySQL server: {} ({})".format(server['name'], server['hostname']))
                else:
                    inner_frames = inspect.getinnerframes(e.__traceback__)
                    found = False
                    for frame in reversed(inner_frames):
                        if any(frame.filename.endswith(i) for i in ['blueprint.py','blueprint.pyc']):
                            found = True
                            current_thread.critical.append("{}: {} (line {})".format(type(e).__name__, str(e).capitalize(), frame.lineno))
                            break
                    if not found:
                        current_thread.critical.append("{}: {}".format(type(e).__name__, str(e).capitalize()))
            
            finally:
                # Add database to the progressed list
                self._progress.append(database)

        # Close SQL Connection
        query_instance.close_sql_connection()
