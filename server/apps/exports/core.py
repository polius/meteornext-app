import paramiko
import subprocess
from io import StringIO

class Core:
    def __init__(self, region):
        self._region = region

    def execute(self, command):
        if self._region['ssh_tunnel']:
            return self.__remote(command)
        return self.__local(command)

    ####################
    # INTERNAL METHODS #
    ####################
    def __local(self, command):
        # Execute Local Command
        p = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Return Result
        return {'stdout': p.stdout.decode('utf-8', errors='ignore').strip(), 'stderr': p.stderr.decode('utf-8', errors='ignore').strip()}

    def __remote(self, command):
        # Init Paramiko SSH Connection
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        password = None if self._region['password'] is None or len(self._region['password'].strip()) == 0 else self._region['password']
        pkey = None if self._region['key'] is None or len(self._region['key'].strip()) == 0 else paramiko.RSAKey.from_private_key(StringIO(self._region['key']), password=password)
        client.connect(self._region['hostname'], port=self._region['port'], username=self._region['username'], password=self._region['password'], pkey=pkey, timeout=10)
        transport = client.get_transport()
        transport.set_keepalive(30)

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
