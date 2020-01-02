from io import StringIO
import os
import sys
import time
import socket
import paramiko
import pymysql
import sshtunnel
import subprocess

class Utils:
    def __init__(self, app, connection=None):
        self._app = app
        self._conn = connection

    def prepare(self, force=False):
        if not self._conn['cross_region']:
            return {'success': True}

        # Init variables
        is_binary = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        script_path = "{}/apps/meteor".format(sys._MEIPASS) if is_binary else "{}/../meteor".format(self._app.root_path)

        # Check SSH Connection
        try:
            self.check_ssh()
        except Exception as e:
            return {'success': False, 'error': "Can't connect to the SSH Region"}

        # Check SSH Path
        if not self.check_ssh_path():
            return {'success': False, 'error': "The user '{}' does not have rwx privileges to the Deploy Path".format(self._conn['username'])}        

        # Check if Meteor is already deployed
        result = self.__ssh("test -d '{}' && printf '1' || printf '0'".format(self._conn['deploy_path']))

        if result['stdout'][0] != '1' or force:
            # Deploy Meteor to the SSH Region
            self.__ssh("mkdir -p {0} && chmod 700 {0} && rm -rf {0}/*".format(self._conn['deploy_path']))
            if not is_binary:
                self.__local('cd {} && rm -rf meteor.tar.gz && tar -czvf meteor.tar.gz . --exclude "logs" --exclude "*.git*" --exclude "*.pyc" --exclude "web" --exclude "credentials.json" --exclude "query_execution.py"'.format(script_path))

            try:
                self.__put("{}/meteor.tar.gz".format(script_path), "{}/meteor.tar.gz".format(self._conn['deploy_path']))
            except Exception as e:
                return {'success': False, 'error': str(e)}
            self.__ssh("cd {} && tar -xvzf meteor.tar.gz -C . && rm -rf meteor.tar.gz".format(self._conn['deploy_path']))
            self.__local('cd {} && rm -rf meteor.tar.gz'.format(script_path))

        # Return Success
        return {'success': True}

    def unprepare(self):
        if not self._conn['cross_region']:
            return {'success': True}

        # Check SSH Connection
        try:
            self.check_ssh()
        except Exception as e:
            return {'success': False, 'error': "Can't connect to the SSH Region"}

        # Remove deployed Meteor
        self.__ssh("rm -rf {}".format(self._conn['deploy_path']))

        # Return Success
        return {'success': True}

    def check_ssh(self):
        pkey = paramiko.RSAKey.from_private_key(StringIO(self._conn['key']))
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(hostname=self._conn['hostname'], port=int(self._conn['port']), username=self._conn['username'], password=self._conn['password'], pkey=pkey, timeout=10)

    def check_sql(self, server):
        attempts = 5
        error = None

        for i in range(attempts):
            try:
                if self._conn:
                    pkey = paramiko.RSAKey.from_private_key(StringIO(self._conn['key']))
                    sshtunnel.SSH_TIMEOUT = 5.0
                    sshtunnel.TUNNEL_TIMEOUT = 5.0
                    with sshtunnel.SSHTunnelForwarder((self._conn['hostname'], int(self._conn['port'])), ssh_username=self._conn['username'], ssh_password=self._conn['password'], ssh_pkey=pkey, remote_bind_address=(server['hostname'], int(server['port']))) as tunnel:
                        conn = pymysql.connect(host='127.0.0.1', port=tunnel.local_bind_port, user=server['username'], passwd=server['password'])
                        conn.close()
                else:
                    conn = pymysql.connect(host=server['hostname'], port=server['port'], user=server['username'], passwd=server['password'])
                return {"success": True}
            except Exception as e:
                error = e
                time.sleep(1)

        raise Exception(error)

    def check_local_path(self, path):
        while not os.path.exists(path) and path != '/':
            path = os.path.normpath(os.path.join(path, os.pardir))
        if os.access(path, os.X_OK | os.W_OK):
            return True
        return False

    def check_ssh_path(self):
        pkey = paramiko.RSAKey.from_private_key(StringIO(self._conn['key']))
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(hostname=self._conn['hostname'], port=int(self._conn['port']), username=self._conn['username'], password=self._conn['password'], pkey=pkey, timeout=10)

        # Open sftp connection
        sftp = client.open_sftp()

        path = self._conn['deploy_path']
        while True:
            try:
                if path == '/':
                    return False
                stat = sftp.lstat(path)
                break
            except Exception:
                path = os.path.normpath("{}/..".format(path))
        path_permissions = str(stat)[:str(stat).find(' ')]
        sftp.close()
        return path_permissions.startswith('drwx')

    ####################
    # Internal Methods #
    ####################
    def __local(self, command):
        # Paramiko Execute Local Command
        client = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Return Execution Output
        return { "stdout": [self.__decode(i) for i in client.stdout.readlines()], "stderr": ''.join(str(v) for v in client.stderr.readlines()) }

    def __ssh(self, command):
        try:
            # Supress Errors Output
            sys_stderr = sys.stderr
            sys.stderr = open('/dev/null', 'w')

            # Init Paramiko SSH Connection
            pkey = paramiko.RSAKey.from_private_key(StringIO(self._conn['key']))
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(hostname=self._conn['hostname'], port=int(self._conn['port']), username=self._conn['username'], password=self._conn['password'], pkey=pkey, timeout=10)

            # Show Errors Output Again
            sys.stderr = sys_stderr

            # Paramiko Execute Command
            stdin, stdout, stderr = client.exec_command(command, get_pty=False)
            stdin.close()

            # Return Execution Output
            return { "stdout": [self.__decode(i) for i in stdout.readlines()], "stderr": ''.join(stderr.readlines()) }

        except socket.error as e:
            raise Exception("Connection Timeout. Can't establish a SSH connection.")

        finally:
            # Paramiko Close Connection
            if client.get_transport() is not None and client.get_transport().is_active():
                client.close()

    def __put(self, local_path, remote_path):
        try:
            # Init Paramiko Connection
            pkey = paramiko.RSAKey.from_private_key(StringIO(self._conn['key']))
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(hostname=self._conn['hostname'], port=int(self._conn['port']), username=self._conn['username'], password=self._conn['password'], pkey=pkey, timeout=10)

            # Open sftp connection
            sftp = client.open_sftp()

            # Upload File
            sftp.put(local_path, remote_path)

        except IOError:
            raise Exception("The current user does not have permissions to write to the provided deployment path.")

        finally:
            if 'sftp' in locals():
                sftp.close()

    def __decode(self, string):
        try:
            return string.decode('utf-8')
        except Exception:
            return string