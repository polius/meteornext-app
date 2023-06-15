import os
import sys
import uuid
import argparse

class server:
    def __init__(self):
        # Init Global Variables
        self._version = '1.0.8'
        self._sentry_dsn = 'https://7de474b9a31148d29d10eb5aea1dff71@o1100742.ingest.sentry.io/6138582'

        # Init args
        args = self.__init_parser()
        if args.deployments:
            self.__deployments()
        elif args.monitoring:
            self.__monitoring()
        elif args.utils:
            self.__utils()
        else:
            self.__init()

    def __init_parser(self):
        parser = argparse.ArgumentParser(description='server')
        parser.add_argument('--deployments', required=False, action='store_true', dest='deployments', help=argparse.SUPPRESS)
        parser.add_argument('--monitoring', required=False, action='store_true', dest='monitoring', help=argparse.SUPPRESS)
        parser.add_argument('--utils', required=False, action='store_true', dest='utils', help=argparse.SUPPRESS)
        args = parser.parse_args()
        return args

    def __init(self):
        from multiprocessing import Process
        from multiprocessing.managers import BaseManager

        # Init Shared License Class
        from license import License
        BaseManager.register('License', License)
        manager = BaseManager()
        manager.start()
        l = manager.License(self._version)

        # Init Node
        node = str(uuid.uuid4())

        # Init Server Api
        from api import Api
        p = Process(target=Api, args=(self._version, l, self._sentry_dsn, node))
        p.start()

        # Init Cron
        from cron import Cron
        try:
            Cron(l, self._sentry_dsn, node)
        except KeyboardInterrupt:
            manager.shutdown()

    def __deployments(self):
        # Import Dependencies
        import connectors.base
        import routes.deployments.deployments

        # Check Execution
        data = self.__check()
        if data is None:
            return

        # Init Sentry
        if data['metadata']['sentry']:
            import sentry_sdk
            sentry_sdk.init(dsn=self._sentry_dsn, environment=data['conf']['license']['access_key'], traces_sample_rate=0)

        # Init License
        class License:
            def __init__(self, resources, sentry):
                self._resources = resources
                self._sentry = sentry
            def get_resources(self):
                return self._resources
            def get_sentry(self):
                return self._sentry
        license = License(data['metadata']['resources'], data['metadata']['sentry'])

        # Init SQL Connection
        conn = connectors.base.Base({"sql": data['conf']['sql']})

        # Check new scheduled & queued executions
        deployments = routes.deployments.deployments.Deployments(license, conn)
        deployments.check_finished()
        deployments.check_recurring()
        deployments.check_scheduled()
        deployments.check_queued()

    def __monitoring(self):
        # Import Dependencies
        import apps.monitor.monitor

        # Check Execution
        data = self.__check()
        if data is None:
            return

        # Init Sentry
        if data['metadata']['sentry']:
            import sentry_sdk
            sentry_sdk.init(dsn=self._sentry_dsn, environment=data['conf']['license']['access_key'], traces_sample_rate=0)

        # Init License
        class License:
            def __init__(self, resources):
                self._resources = resources
            def get_resources(self):
                return self._resources
        license = License(data['metadata']['resources'])

        # Start monitoring servers
        monitoring = apps.monitor.monitor.Monitor(license, {"sql": data['conf']['sql']})
        monitoring.start()
        
    def __utils(self):
        # Import Dependencies
        import connectors.pool
        import routes.utils.utils

        # Check Execution
        data = self.__check()
        if data is None:
            return

        # Init Sentry
        if data['metadata']['sentry']:
            import sentry_sdk
            sentry_sdk.init(dsn=self._sentry_dsn, environment=data['conf']['license']['access_key'], traces_sample_rate=0)

        # Init License
        class License:
            def __init__(self, resources):
                self._resources = resources
            def get_resources(self):
                return self._resources
        license = License(data['metadata']['resources'])

        # Init SQL Connection
        conn = connectors.pool.Pool(data['conf']['sql'])

        # Check queued executions
        utils = routes.utils.utils.Utils(license, conn)
        utils.check_queued()

    ####################
    # Internal Methods #
    ####################
    def __check(self):
        # Import Dependencies
        import json
        import requests
        import connectors.base

        # Retrieve base path
        bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        base_path = os.path.realpath(os.path.dirname(sys.executable)) if bin else os.path.realpath(os.path.dirname(sys.argv[0]))

        # Check Api
        if not os.path.exists(f"{base_path}/server.pid"):
            return

        # Load 'server.conf' file
        try:
            with open(f"{base_path}/server.conf") as file_open:
                conf = json.load(file_open)
        except FileNotFoundError:
            return

        # Get Metadata
        port = 80 if bin else 5000
        response = requests.get(f"http://127.0.0.1:{port}/api/metadata", allow_redirects=False)
        metadata = json.loads(response.text)

        # Check license
        if not metadata['enabled']:
            return

        # Init SQL Connection
        conn = connectors.base.Base({"sql": conf['sql']})

        # Check master node
        try:
            result = conn.execute(query="SELECT type, pid FROM nodes WHERE id = %s", args=(metadata['node']))
            if len(result) == 0 or result[0]['type'] != 'master':
                return
        finally:
            # Close SQL Connection
            conn.stop()

        # Return data
        return {"conf": conf, "metadata": metadata}

if __name__ == '__main__':
    server()
