from io import StringIO
import os
import sys
import time
import paramiko
import pymysql
import sshtunnel

class Utils:
    def __init__(self, connection=None):
        self._conn = connection

    def check_ssh(self):
        # Supress Errors Output
        sys_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')

        try:
            pkey = paramiko.RSAKey.from_private_key(StringIO(self._conn['key']))
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(hostname=self._conn['hostname'], port=int(self._conn['port']), username=self._conn['username'], password=self._conn['password'], pkey=pkey, timeout=10)
            client.close()
        finally:
            # Supress Errors Output
            sys_stderr = sys.stderr
            sys.stderr = open(os.devnull, 'w')

    def check_sql(self, server):
        f = open(os.devnull, 'w')
        stdout = sys.stdout
        stderr = sys.stderr
        sys.stdout = f
        sys.stderr = f

        try:
            if self._conn:
                pkey = paramiko.RSAKey.from_private_key(StringIO(self._conn['key']))
                sshtunnel.SSH_TIMEOUT = 10.0
                with sshtunnel.SSHTunnelForwarder((self._conn['hostname'], int(self._conn['port'])), ssh_username=self._conn['username'], ssh_password=self._conn['password'], ssh_pkey=pkey, remote_bind_address=(server['hostname'], int(server['port'])), threaded=False) as tunnel:
                    conn = pymysql.connect(host='127.0.0.1', port=tunnel.local_bind_port, user=server['username'], passwd=server['password'])
                    conn.close()
            else:
                conn = pymysql.connect(host=server['hostname'], port=int(server['port']), user=server['username'], passwd=server['password'])
            return {"success": True}
        finally:
            sys.stdout = stdout
            sys.stderr = stderr

    def check_local_path(self, path):
        while not os.path.exists(path) and path != '/':
            path = os.path.normpath(os.path.join(path, os.pardir))
        if os.access(path, os.X_OK | os.W_OK):
            return True
        return False

    def get_ip(self):
        # from flask import request
        # ip = request.headers.getlist("X-Forwarded-For")[0] if request.headers.getlist("X-Forwarded-For") else request.remote_addr
        pass