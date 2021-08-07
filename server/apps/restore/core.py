import sys
import time
import json
import paramiko
import subprocess
from io import StringIO

class Core:
    def __init__(self, sql, restore_id, region):
        self._sql = sql
        self._id = restore_id
        self._region = region
        self._now = None
        # Properties
        self._stop = False
        self._client = None
        self._sftp = None

    def stop(self):
        self._stop = True

    def execute(self, command):
        if self._region['ssh_tunnel']:
            return self.__remote(command)
        return self.__local(command)

    def put(self, local_path, remote_path):
        # Init Paramiko Connection
        self._client = paramiko.SSHClient()
        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(paramiko.WarningPolicy())
        password = None if self._region['password'] is None or len(self._region['password'].strip()) == 0 else self._region['password']
        pkey = None if self._region['key'] is None or len(self._region['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._region['key']), password=password)
        self._client.connect(self._region['hostname'], port=self._region['port'], username=self._region['username'], password=self._region['password'], pkey=pkey, banner_timeout=60)

        # Open sftp connection
        self._sftp = self._client.open_sftp()

        # Upload File
        self._sftp.put(localpath=local_path, remotepath=remote_path, callback=self.__put_callback)

        # Close Connection
        try:
            self._sftp.close()
            self._client.close()
        except Exception:
            pass

    ####################
    # INTERNAL METHODS #
    ####################
    def __local(self, command):
        # Execute Local Command
        p = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Return Result
        return {'stdout': p.stdout.decode('utf-8', errors='ignore').strip(), 'stderr': p.stderr.decode('utf-8', errors='ignore').strip()}

    def __remote(self, command):
        # Supress Errors Output
        # sys_stderr = sys.stderr
        # sys.stderr = open('/dev/null', 'w')

        # Init Paramiko SSH Connection
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        password = None if self._region['password'] is None or len(self._region['password'].strip()) == 0 else self._region['password']
        pkey = None if self._region['key'] is None or len(self._region['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._region['key']), password=password)
        client.connect(self._region['hostname'], port=self._region['port'], username=self._region['username'], password=self._region['password'], pkey=pkey, timeout=10)
        transport = client.get_transport()
        transport.set_keepalive(30)

        # Show Errors Output Again
        # sys.stderr = sys_stderr

        # Paramiko Execute Command
        stdin, stdout, stderr = client.exec_command(command, get_pty=False)
        stdout._set_mode('b')
        stderr._set_mode('b')
        stdin.close()

        # Build Response Data
        data = {'stdout': '\n'.join([i.decode('utf-8', errors='ignore').strip() for i in stdout.readlines()]), 'stderr': '\n'.join([i.decode('utf-8', errors='ignore').strip() for i in stderr.readlines()])}

        # Close Connection
        client.close()

        # Return Result
        return data

    def __put_callback(self, transferred, total):
        # Check stop flag
        if self._stop:
            try:
                self._sftp.close()
                self._client.close()
            except Exception:
                pass
        # Update progress
        upload = {"transferred": transferred, "value": int(transferred / total * 100)}
        if self._now is None or int(time.time() - self._now) > 2 or transferred == total:
            # Update restore upload progress
            query = """
                UPDATE `restore`
                SET `upload` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(json.dumps(upload), self._id))
