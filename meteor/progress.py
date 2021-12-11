import json
from datetime import datetime
from connector import connector

class progress:
    def __init__(self, args, imports):
        self._args = args
        self._config = imports.config
        self._progress = {}
        self._sql = self.__connector()

    def start(self, pid):
        self._sql.start()
        logs = 'amazon_s3' if self._config['amazon_s3']['enabled'] else 'local'
        query = "UPDATE executions SET status = 'IN PROGRESS', logs = %s, started = %s, pid = %s WHERE id = %s".format()
        self._sql.execute(query=query, args=(logs, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), pid, self._config['params']['id']), database=self._config['meteor_next']['database'])

    def end(self, execution_status):
        status = 'SUCCESS' if execution_status == 0 else 'WARNING' if execution_status == 1 else 'STOPPED'
        query = "UPDATE executions SET status = %s, ended = %s, error = 0 WHERE id = %s"
        self._sql.execute(query=query, args=(status, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), self._config['params']['id']), database=self._config['meteor_next']['database'])
        self._sql.stop()

    def error(self, error_msg):
        self._progress['error'] = str(error_msg)
        query = "UPDATE executions SET status = 'FAILED', progress = %s, ended = %s, error = 1 WHERE id = %s"
        self._sql.execute(query=query, args=(json.dumps(self._progress), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), self._config['params']['id']), database=self._config['meteor_next']['database'])

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
            self._progress['execution'] = []
        self._progress['execution'] = value
        self.__store()

    def track_logs(self, value):
        if 'logs' not in self._progress:
            self._progress['logs'] = []
        if 'message' not in value:
            self._progress['logs'][-1]['status'] = value['status']
        else:
            self._progress['logs'].append(value)
        self.__store()

    def track_tasks(self, value):
        if 'tasks' not in self._progress:
            self._progress['tasks'] = []
        if 'message' not in value:
            self._progress['tasks'][-1]['status'] = value['status']
        else:
            self._progress['tasks'].append(value)
        self.__store()

    def track_queries(self, value):
        if 'queries' not in self._progress:
            self._progress['queries'] = {}
        self._progress['queries'] = value
        self.__store()

    def start_region_update(self, region_id):
        sql = self.__connector()
        sql.start()
        query = """
            INSERT INTO regions_update (execution_id, region_id)
            SELECT *
            FROM (
                SELECT %(execution_id)s, %(region_id)s
            ) t
            WHERE NOT EXISTS (
                SELECT *
                FROM regions_update ru
                JOIN regions r1 ON r1.id = ru.region_id
                JOIN regions r2 ON r2.id = %(region_id)s
                WHERE ru.region_id = %(region_id)s
                OR (
                    r1.hostname = r2.hostname
                    AND r2.port = r2.port
                )
            )
        """
        args = {'execution_id': self._config['params']['id'], 'region_id': region_id}
        result = sql.execute(query=query, args=args, database=self._config['meteor_next']['database'])
        sql.stop()
        return result['query_result'] > 0

    def finish_region_update(self, region_id):
        sql = self.__connector()
        sql.start()
        query = """
            DELETE FROM regions_update
            WHERE region_id = %s
        """
        sql.execute(query=query, args=(region_id), database=self._config['meteor_next']['database'])
        sql.stop()

    def check_region_update(self, region_id):
        sql = self.__connector()
        sql.start()
        query = """
            SELECT COUNT(*) AS 'n'
            FROM regions_update
            WHERE region_id = %s
        """
        result = sql.execute(query=query, args=(region_id), database=self._config['meteor_next']['database'])['query_result'][0]['n'] == 0
        sql.stop()
        return result

    def __store(self):
        self._progress['updated'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        query = "UPDATE executions SET progress = %s WHERE id = %s"
        self._sql.execute(query=query, args=(json.dumps(self._progress), self._config['params']['id']), database=self._config['meteor_next']['database'])

    def __connector(self):
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
        return connector({"ssh": ssh, "sql": sql})
