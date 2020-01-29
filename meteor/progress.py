import json
from datetime import datetime
from connector import connector

class progress:
    def __init__(self, args, imports):
        self._args = args
        self._credentials = imports.credentials
        self._progress = {}
        self._sql = None

        # Init Connection
        self.__init()

    def __init(self):
        ssh = {"enabled": False}
        sql = {"engine": "MySQL", "hostname": self._credentials['meteor_next']['hostname'], "port": self._credentials['meteor_next']['port'], "username": self._credentials['meteor_next']['username'], "password": self._credentials['meteor_next']['password'], "database": self._credentials['meteor_next']['database']}
        self._sql = connector({"ssh": ssh, "sql": sql})

    def start(self, pid):
        if self.__enabled():
            # Init the connection
            self._sql.start()
            # Track progress
            engine = 'amazon_s3' if self._credentials['amazon_s3']['enabled'] else 'local'
            uri = self._args.execution_path[self._args.execution_path.rfind('/')+1:]
            query = "UPDATE deployments_{} SET status = 'IN PROGRESS', uri = '{}', engine = '{}', started = '{}', pid = '{}' WHERE id = {}".format(self._args.execution_mode, uri, engine, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), pid, self._args.execution_id)
            self._sql.execute(query, self._credentials['meteor_next']['database'])

    def end(self, execution_status):
        if self.__enabled():
            status = 'SUCCESS' if execution_status == 0 else 'WARNING' if execution_status == 1 else 'STOPPED'
            query = "UPDATE deployments_{} SET status = '{}', ended = '{}', error = 0 WHERE id = {}".format(self._args.execution_mode, status, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), self._args.execution_id)
            self._sql.execute(query, self._credentials['meteor_next']['database'])
            self._sql.stop()

    def error(self, error_msg):
        if self.__enabled():
            self._progress['error'] = str(error_msg).replace('"', '\\"').replace("\n", "\\n")
            progress = json.dumps(self._progress).replace("'", "\\'")
            query = "UPDATE deployments_{} SET status = 'FAILED', progress = '{}', ended = '{}', error = 1 WHERE id = {}".format(self._args.execution_mode, progress, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), self._args.execution_id)
            self._sql.execute(query, self._credentials['meteor_next']['database'])
            self._sql.stop()

    def track_syntax(self, value):
        if self.__enabled():
            if 'syntax' not in self._progress:
                self._progress['syntax'] = []
            self._progress['syntax'].append(value)
            self.__store()

    def track_validation(self, value):
        if self.__enabled():
            self._progress['validation'] = value
            self.__store()
    
    def track_execution(self, value):
        if self.__enabled():
            if 'execution' not in self._progress:
                self._progress['execution'] = {}
            self._progress['execution'] = value
            self.__store()

    def track_logs(self, value):
        if self.__enabled():
            if 'logs' not in self._progress:
                self._progress['logs'] = []
            self._progress['logs'].append(value)
            self.__store()

    def track_tasks(self, value):
        if self.__enabled():
            if 'tasks' not in self._progress:
                self._progress['tasks'] = []
            self._progress['tasks'].append(value)
            self.__store()

    def track_queries(self, value):
        if self.__enabled():
            if 'queries' not in self._progress:
                self._progress['queries'] = {}
            self._progress['queries'] = value
            self.__store()

    def __store(self):
        self._progress['updated'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        progress = json.dumps(self._progress).replace("'", "\\\'")
        query = "UPDATE deployments_{} SET progress = '{}' WHERE id = {}".format(self._args.execution_mode, progress, self._args.execution_id)
        self._sql.execute(query, self._credentials['meteor_next']['database'])

    def __enabled(self):
        if 'meteor_next' in self._credentials and self._credentials['meteor_next']['enabled']:
            return True
        else:
            return False