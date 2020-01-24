import sys
import time
import pymysql
import paramiko
import sshtunnel
import threading

class validate_regions:
    def __init__(self, args, credentials, region):
        self._args = args
        self._credentials = credentials
        self._region = region

    def validate(self):
        region_type = '[SSH]  ' if self._region['ssh']['enabled'] else '[LOCAL]'
        print("--> {} Region '{}' Started...".format(region_type, self._region['region']))

        # Get current thread 
        current_thread = threading.current_thread()

        # SSH Validation
        if self._region['ssh']['enabled']:
            try:
                self.__validate_ssh()
            except Exception as e:
                current_thread.progress = {'region': self._region['region'], 'success': False, 'error': str(e)}
                print("--> {} Region '{}' Failed.".format(region_type, self._region['region']))
                return

        # SQL Validation
        progress = {'region': self._region['region'], 'errors': []}
        threads = []
        for server in self._region['sql']:
            t = threading.Thread(target=self.__validate_sql, args=(server,))
            threads.append(t)
            t.progress = {}
            t.start()

        # Wait threads
        for t in threads:
            t.join()

        # Get values
        connection_succeeded = True
        for t in threads:
            connection_succeeded &= t.progress['success']
            if t.progress['success'] == False:
                print("    [{}/SQL] {} {}".format(self._region['region'], t.progress['sql'], t.progress['error']))
                progress['errors'].append({'server': t.progress['sql'], 'error': t.progress['error'].replace('"', '\\"')})

        # In case of no errors, remove the 'errors' key
        if len(progress['errors']) == 0:
            del progress['errors']

        # Print status
        if connection_succeeded:
            print("--> {} Region '{}' Finished.".format(region_type, self._region['region']))
        else:
            print("--> {} Region '{}' Failed.".format(region_type, self._region['region']))

        # Return validation status
        progress['success'] = connection_succeeded
        current_thread.progress = progress

    def __validate_ssh(self):
        # Supress Errors Output
        sys_stderr = sys.stderr
        sys.stderr = open('/dev/null', 'w')
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(hostname=self._region['ssh']['hostname'], port=int(self._region['ssh']['port']), username=self._region['ssh']['username'], password=self._region['ssh']['password'], key_filename=self._region['ssh']['key'], timeout=10)
            client.close()
        finally:
            # Show Errors Output Again
            sys.stderr = sys_stderr

    def __validate_sql(self, server):
        # Supress Errors Output
        sys_stderr = sys.stderr
        sys.stderr = open('/dev/null', 'w')

        current_thread = threading.current_thread()
        error = None
        attempts = 5

        for i in range(attempts):
            try:
                if self._region['ssh']['enabled']:
                    ssh_pkey = paramiko.RSAKey.from_private_key_file(self._region['ssh']['key'])
                    with sshtunnel.SSHTunnelForwarder((self._region['ssh']['hostname'], int(self._region['ssh']['port'])), ssh_username=self._region['ssh']['username'], ssh_password=self._region['ssh']['password'], ssh_pkey=ssh_pkey, remote_bind_address=(server['hostname'], int(server['port']))) as tunnel:
                        conn = pymysql.connect(host='127.0.0.1', port=tunnel.local_bind_port, user=server['username'], passwd=server['password'])
                        conn.close()
                else:
                    conn = pymysql.connect(host=server['hostname'], port=server['port'], user=server['username'], passwd=server['password'])
                    conn.close()
                current_thread.progress = {"region": self._region['region'], "sql": server['name'], "success": True}
                break

            except Exception as e:
                error = e
                time.sleep(1)

        # Show Errors Output Again
        sys.stderr = sys_stderr

        if error is not None:
            current_thread.progress = {"region": self._region['region'], "sql": server['name'], "success": False, "error": str(error).replace('\n','')}