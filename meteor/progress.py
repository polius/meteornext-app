import json
from datetime import datetime
from connector import connector

class progress:
    def __init__(self, args, imports):
        self._args = args
        self._config = imports.config
        self._progress = {}
        self._sql = None

        # Init Connection
        self.__init()

    def __init(self):
        ssh = {"enabled": False}
        sql = {
            "engine": "MySQL",
            "hostname": self._config['meteor_next']['hostname'],
            "port": self._config['meteor_next']['port'],
            "username": self._config['meteor_next']['username'],
            "password": self._config['meteor_next']['password'],
            "database": self._config['meteor_next']['database'],
            "autocommit": True,
            "ssl_ca_certificate": self._config['meteor_next']['ssl_ca_certificate'],
            "ssl_client_certificate": self._config['meteor_next']['ssl_client_certificate'],
            "ssl_client_key": self._config['meteor_next']['ssl_client_key'],
            "ssl_verify_ca": self._config['meteor_next']['ssl_verify_ca']
        }
        self._sql = connector({"ssh": ssh, "sql": sql})

    def start(self, pid):
        # Init the connection
        self._sql.start()
        # Track progress
        engine = 'amazon_s3' if self._config['amazon_s3']['enabled'] else 'local'
        uri = self._args.path[self._args.path.rfind('/')+1:]
        query = "UPDATE deployments_{} SET status = 'IN PROGRESS', uri = '{}', engine = '{}', started = '{}', pid = '{}' WHERE id = {}".format(self._config['params']['mode'], uri, engine, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), pid, self._config['params']['id'])
        self._sql.execute(query=query, database=self._config['meteor_next']['database'])

    def end(self, execution_status):
        status = 'SUCCESS' if execution_status == 0 else 'WARNING' if execution_status == 1 else 'STOPPED'
        query = "UPDATE deployments_{} SET status = '{}', ended = '{}', error = 0 WHERE id = {}".format(self._config['params']['mode'], status, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), self._config['params']['id'])
        self._sql.execute(query=query, database=self._config['meteor_next']['database'])
        self._sql.stop()

    def error(self, error_msg):
        self._progress['error'] = str(error_msg).replace('"', '\\"').replace("\n", "\\n")
        progress = json.dumps(self._progress).replace("'", "\\'")
        query = "UPDATE deployments_{} SET status = 'FAILED', progress = '{}', ended = '{}', error = 1 WHERE id = {}".format(self._config['params']['mode'], progress, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), self._config['params']['id'])
        self._sql.execute(query=query, database=self._config['meteor_next']['database'])
        self._sql.stop()

    def track_syntax(self, value):
        if 'syntax' not in self._progress:
            self._progress['syntax'] = []
        self._progress['syntax'].append(value)
        self.__store()

    def track_validation(self, value):
        self._progress['validation'] = value
        self.__store()
    
    def track_execution(self, value):
        if 'execution' not in self._progress:
            self._progress['execution'] = {}
        self._progress['execution'] = value
        self.__store()

    def track_logs(self, value):
        if 'logs' not in self._progress:
            self._progress['logs'] = []
        self._progress['logs'].append(value)
        self.__store()

    def track_tasks(self, value):
        if 'tasks' not in self._progress:
            self._progress['tasks'] = []
        self._progress['tasks'].append(value)
        self.__store()

    def track_queries(self, value):
        if 'queries' not in self._progress:
            self._progress['queries'] = {}
        self._progress['queries'] = value
        self.__store()

    def start_region_update(self, region_id):
        query = """
            INSERT INTO regions_update (execution_id, execution_mode, region_id)
            SELECT *
            FROM (
                SELECT %(execution_id)s, %(execution_mode)s, %(region_id)s
            ) t
            WHERE NOT EXISTS (
                SELECT *
                FROM regions_update
                WHERE region_id = %(region_id)s
            )
        """
        args = {'execution_id': self._config['params']['id'], 'execution_mode': self._config['params']['mode'], 'region_id': region_id}
        result = self._sql.execute(query=query, args=args, database=self._config['meteor_next']['database'])
        return result['query_result'] > 0

    def finish_region_update(self, region_id):
        query = """
            DELETE FROM regions_update
            WHERE region_id = %s
        """
        self._sql.execute(query=query, args=(region_id), database=self._config['meteor_next']['database'])

    def check_region_update(self, region_id):
        query = """
            SELECT COUNT(*) AS 'n'
            FROM regions_update
            WHERE region_id = %s
        """
        return self._sql.execute(query=query, args=(region_id), database=self._config['meteor_next']['database'])['query_result'][0]['n'] == 0

    def __store(self):
        self._progress['updated'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        progress = json.dumps(self._progress).replace("'", "\\\'")
        query = "UPDATE deployments_{} SET progress = '{}' WHERE id = {}".format(self._config['params']['mode'], progress, self._config['params']['id'])
        self._sql.execute(query=query, database=self._config['meteor_next']['database'])
