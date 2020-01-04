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
        # Init variables
        self._is_binary = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._script_path = "{}/apps".format(sys._MEIPASS) if self._is_binary else "{}/../meteor".format(self._app.root_path)

    def prepare(self, force=False):
        # Check Deployment
        deploy_status = self.check_ssh_deploy()
        if 'error' in deploy_status:
            return deploy_status

        if not deploy_status['exists'] or force:
            # Deploy Meteor to the SSH Region
            self.__ssh("mkdir -p {0} && chmod 700 {0} && rm -rf {0}/*".format(self._conn['deploy_path']))
            if not self._is_binary:
                self.__local('cd {} && rm -rf meteor.tar.gz && tar -czvf meteor.tar.gz . --exclude "logs" --exclude "*.git*" --exclude "*.pyc" --exclude "web" --exclude "credentials.json" --exclude "query_execution.py"'.format(self._script_path))

            try:
                self.__put("{}/meteor.tar.gz".format(self._script_path), "{}/meteor.tar.gz".format(self._conn['deploy_path']))
            except Exception as e:
                return {'success': False, 'error': str(e)}
            self.__ssh("cd {} && tar -xvzf meteor.tar.gz -C . && rm -rf meteor.tar.gz".format(self._conn['deploy_path']))

        # Return Success
        return {'success': True}

    def unprepare(self):
        # Check SSH Connection
        try:
            self.check_ssh()
        except Exception as e:
            return {'success': False, 'error': "Can't connect to the SSH Region"}

        # Remove deployed Meteor
        self.__ssh("rm -rf {}".format(self._conn['deploy_path']))

        # Return Success
        return {'success': True}

    def check_ssh_deploy(self):
        # Check SSH Connection
        try:
            self.check_ssh()
        except Exception as e:
            return {'error': "Can't connect to the SSH Region"}

        # Check SSH Path
        if not self.check_ssh_path():
            return {'error': "The user '{}' does not have rwx privileges to the Deploy Path".format(self._conn['username'])}        

        # Check if Meteor is already deployed with the same version
        result = self.__ssh("test -f '{}/version.txt' && printf '1' || printf '0'".format(self._conn['deploy_path']))['stdout'][0]
        if result == '0':
            return {'exists': False}

        ssh_version = self.__ssh("cat {}/version.txt".format(self._conn['deploy_path']))['stdout']
        if len(ssh_version) == 0:
            return {'exists': False}
        else:
            ssh_version = ssh_version[0].replace('\n', '')

        # Get Local Version
        version_path = "{}/apps/meteor/version.txt".format(sys._MEIPASS) if self._is_binary else "{}/../meteor/version.txt".format(self._app.root_path)
        with open(version_path) as file_content:
            local_version = file_content.read().replace('\n', '')

        # Compare Local & SSH Version
        return {'exists': local_version == ssh_version}

    def check_ssh(self):
        pkey = paramiko.RSAKey.from_private_key(StringIO(self._conn['key']))
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(hostname=self._conn['hostname'], port=int(self._conn['port']), username=self._conn['username'], password=self._conn['password'], pkey=pkey, timeout=10)

    def check_sql(self, server):
        f = open(os.devnull, 'w')
        stdout = sys.stdout
        stderr = sys.stderr
        sys.stdout = f
        sys.stderr = f

        attempts = 3
        error = None

        for i in range(attempts):
            try:
                if self._conn:
                    pkey = paramiko.RSAKey.from_private_key(StringIO(self._conn['key']))
                    with sshtunnel.SSHTunnelForwarder((self._conn['hostname'], int(self._conn['port'])), ssh_username=self._conn['username'], ssh_password=self._conn['password'], ssh_pkey=pkey, remote_bind_address=(server['hostname'], int(server['port'])), threaded=False) as tunnel:
                        sys.stdout = f
                        conn = pymysql.connect(host='127.0.0.1', port=tunnel.local_bind_port, user=server['username'], passwd=server['password'])
                        conn.close()
                else:
                    conn = pymysql.connect(host=server['hostname'], port=int(server['port']), user=server['username'], passwd=server['password'])
                return {"success": True}
            except Exception as e:
                error = e
                time.sleep(1)
            finally:
                sys.stdout = stdout
                sys.stderr = stderr

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