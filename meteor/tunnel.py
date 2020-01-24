import sys
import time
import paramiko
import sshtunnel

class tunnel:
    def __init__(self, server):
        self._server = server
        self._tunnel = None

    @property
    def tunnel(self):
        return self._tunnel

    def open(self):
        if not self._server['ssh']['enabled']:
            return

        error = None
        attempts = 10

        for i in range(attempts):
            try:
                ssh_pkey = paramiko.RSAKey.from_private_key_file(self._server['ssh']['key'])
                self._tunnel = sshtunnel.SSHTunnelForwarder((self._server['ssh']['hostname'], int(self._server['ssh']['port'])), ssh_username=self._server['ssh']['username'], ssh_password=self._server['ssh']['password'], ssh_pkey=ssh_pkey, remote_bind_address=(self._server['sql']['hostname'], int(self._server['sql']['port'])))
                self._tunnel.start()
                return

            except Exception as e:
                error = e
                self.close()
                time.sleep(2)

        if error is not None:
            raise error

    def close(self):
        try:
            self._tunnel.close()
        except Exception as e:
            pass

    def ping(self):
        self._tunnel.check_tunnels()
