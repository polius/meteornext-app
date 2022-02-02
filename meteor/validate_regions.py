import sys
import time
import pymysql
import tempfile
import paramiko
import sshtunnel
import threading

from region import Region

class validate_regions:
    def __init__(self, args, region, progress):
        self._args = args
        self._region = region
        self._progress = progress
        self._Region = Region(args, region)

    def validate(self):
        # Get current thread 
        current_thread = threading.current_thread()

        # SSH Validation
        if self._region['ssh']['enabled']:
            try:
                self.__validate_ssh()
            except Exception as e:
                current_thread.progress = {'id': self._region['id'], 'success': False, 'error': str(e)[0].upper() + str(e)[1:]}
                return

        if not current_thread.alive:
            return

        # SQL Validation
        progress = {'id': self._region['id'], 'errors': []}
        threads = []
        for server in self._region['sql']:
            t = threading.Thread(target=self.__validate_sql, args=(server,))
            threads.append(t)
            t.progress = {}
            t.alive = current_thread.alive
            t.start()

        # Wait threads
        for t in threads:
            t.join()

        # Get values
        connection_succeeded = True
        for t in threads:
            connection_succeeded &= t.progress['success']
            if not t.progress['success']:
                progress['errors'].append({'id': t.progress['id'], 'name': t.progress['name'], 'shared': t.progress['shared'], 'error': t.progress['error'].replace('"', '\\"')})

        # In case of no errors, remove the 'errors' key
        if len(progress['errors']) == 0:
            del progress['errors']

        # Return validation status
        progress['success'] = connection_succeeded
        current_thread.progress = progress

    def __validate_ssh(self):
        # Get current thread 
        current_thread = threading.current_thread()

        # Supress Errors Output
        sys_stderr = sys.stderr
        sys.stderr = open('/dev/null', 'w')

        # Validate SSH Connection
        error = None
        for _ in range(3):
            try:
                if not current_thread.alive:
                    break
                client = paramiko.SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.WarningPolicy())
                client.connect(hostname=self._region['ssh']['hostname'], port=int(self._region['ssh']['port']), username=self._region['ssh']['username'], password=self._region['ssh']['password'], key_filename=self._region['ssh']['key'], timeout=10)
                client.close()
                error = None
                break
            except Exception as e:
                error = e

        # Show Errors Output Again
        sys.stderr = sys_stderr

        # Raise Exception if validation failed
        if error:
            raise error

        # Validate SSH Meteor Version
        if self._region['ssh']['enabled']:
            updated = self._Region.check_version()
            if not updated:
                proceed = self._progress.start_region_update(self._region['id'])
                if proceed:
                    try:
                        self._Region.upload_binary()
                    finally:
                        self._progress.finish_region_update(self._region['id'])
                else:
                   finished = self._progress.check_region_update(self._region['id'])
                   while not finished:
                       time.sleep(1)
                       finished = self._progress.check_region_update(self._region['id'])

    def __validate_sql(self, server):
        # Supress Errors Output
        sys_stderr = sys.stderr
        sys.stderr = open('/dev/null', 'w')

        current_thread = threading.current_thread()
        error = None
        attempts = 3

        for _ in range(attempts):
            try:
                # Get SSL
                ssl = self.__get_ssl(server)
                if self._region['ssh']['enabled']:
                    ssh_pkey = paramiko.RSAKey.from_private_key_file(self._region['ssh']['key'], password=self._region['ssh']['password'])
                    sshtunnel.SSH_TIMEOUT = 5.0
                    with sshtunnel.SSHTunnelForwarder((self._region['ssh']['hostname'], int(self._region['ssh']['port'])), ssh_username=self._region['ssh']['username'], ssh_password=self._region['ssh']['password'], ssh_pkey=ssh_pkey, remote_bind_address=(server['hostname'], int(server['port']))) as tunnel:
                        conn = pymysql.connect(host='127.0.0.1', port=tunnel.local_bind_port, user=server['username'], passwd=server['password'], ssl_ca=ssl['ssl_ca'], ssl_cert=ssl['ssl_cert'], ssl_key=ssl['ssl_key'], ssl_verify_cert=ssl['ssl_verify_cert'], ssl_verify_identity=ssl['ssl_verify_identity'])
                        conn.close()
                else:
                    conn = pymysql.connect(host=server['hostname'], port=int(server['port']), user=server['username'], passwd=server['password'], ssl_ca=ssl['ssl_ca'], ssl_cert=ssl['ssl_cert'], ssl_key=ssl['ssl_key'], ssl_verify_cert=ssl['ssl_verify_cert'], ssl_verify_identity=ssl['ssl_verify_identity'])
                    conn.close()
                current_thread.progress = {"id": server['id'], "name": server['name'], "shared": server['shared'], "success": True}
                error = None
                break
            except Exception as e:
                error = e
                time.sleep(2)
            finally:
                # Close SSL
                self.__close_ssl(ssl)

        # Show Errors Output Again
        sys.stderr = sys_stderr

        if error:
            current_thread.progress = {"id": server['id'], "name": server['name'], "shared": server['shared'], "success": False, "error": str(error).replace('\n','')}

    def __get_ssl(self, server):
        ssl = {'ssl_ca': None, 'ssl_cert': None, 'ssl_key': None, 'ssl_verify_cert': None, 'ssl_verify_identity': None}
        if 'ssl' not in server or not server['ssl']:
            return ssl
        # Generate CA Certificate
        if server['ssl_ca_certificate']:
            ssl['ssl_ca_file'] = tempfile.NamedTemporaryFile()
            ssl['ssl_ca_file'].write(server['ssl_ca_certificate'].encode())
            ssl['ssl_ca_file'].flush()
            ssl['ssl_ca'] = ssl['ssl_ca_file'].name
        # Generate Client Certificate
        if server['ssl_client_certificate']:
            ssl['ssl_cert_file'] = tempfile.NamedTemporaryFile()
            ssl['ssl_cert_file'].write(server['ssl_client_certificate'].encode())
            ssl['ssl_cert_file'].flush()
            ssl['ssl_cert'] = ssl['ssl_cert_file'].name
        # Generate Client Key
        if server['ssl_client_key']:
            ssl['ssl_key_file'] = tempfile.NamedTemporaryFile()
            ssl['ssl_key_file'].write(server['ssl_client_key'].encode())
            ssl['ssl_key_file'].flush()
            ssl['ssl_key'] = ssl['ssl_key_file'].name
        # Add optional parameters
        ssl['ssl_verify_cert'] = server['ssl_verify_ca'] == 1
        ssl['ssl_verify_identity'] = server['ssl_verify_ca'] == 1
        # Return SSL Data
        return ssl

    def __close_ssl(self, ssl):
        if 'ssl_ca_file' in ssl:
            ssl['ssl_ca_file'].close()
        if 'ssl_cert_file' in ssl:
            ssl['ssl_cert_file'].close()
        if 'ssl_key_file' in ssl:
            ssl['ssl_key_file'].close()
