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
        # PUT Timer
        self._now = None

    def execute(self, command):
        if self._region['ssh_tunnel']:
            return self.__remote(command)
        return self.__local(command)

    def put(self, local_path, remote_path): 
        exception = None
        for _ in range(1):
            try:
                # Init Paramiko Connection
                client = paramiko.SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.WarningPolicy())
                password = None if self._region['password'] is None or len(self._region['password'].strip()) == 0 else self._region['password']
                pkey = None if self._region['key'] is None or len(self._region['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._region['key']), password=password)
                client.connect(self._region['hostname'], port=self._region['port'], username=self._region['username'], password=self._region['password'], pkey=pkey, banner_timeout=60)

                # Open sftp connection
                sftp = client.open_sftp()

                # Upload File
                sftp.put(localpath=local_path, remotepath=remote_path, callback=self.__put_progress)
                
                # Close Connection
                try:
                    sftp.close()
                    client.close()
                except Exception:
                    pass
                finally:
                    return

            except Exception as e:
                exception = e
                time.sleep(2)
        raise exception

    ####################
    # INTERNAL METHODS #
    ####################
    def __local(self, command):
        # Execute Local Command
        p = subprocess.run(command, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Return Result
        return {'stdout': p.stdout.strip(), 'stderr': p.stderr.strip()}

    def __remote(self, command):
        retries = 6
        exception = None
        for _ in range(retries):
            try:
                # Supress Errors Output
                sys_stderr = sys.stderr
                sys.stderr = open('/dev/null', 'w')

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
                sys.stderr = sys_stderr

                # Paramiko Execute Command
                stdin, stdout, stderr = client.exec_command(command, get_pty=False)
                stdin.close()

                data = {'stdout': '\n'.join([i.strip() for i in stdout.readlines()]), 'stderr': '\n'.join([i.strip() for i in stderr.readlines()])}

                # Close Connection
                try:
                    client.close()
                except Exception:
                    pass

                # Return Result
                return data

            except Exception as e:
                exception = e
        raise exception

    def __put_progress(self, transferred, total):
        upload = {"transferred": transferred, "value": int(transferred / total * 100)}
        if self._now is None or int(time.time() - self._now) > 2 or transferred == total:
            # Update restore upload progress
            query = """
                UPDATE `restore`
                SET `upload` = %s
                WHERE `id` = %s
            """
            self._sql.execute(query, args=(json.dumps(upload), self._id))
