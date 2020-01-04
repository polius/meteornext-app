#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import socket
import subprocess
import threading
import pymysql
import signal
import sys
import time
import traceback
import warnings
import shutil
import tarfile
import hashlib
import paramiko
import sshtunnel
from colors import colored

warnings.filterwarnings("ignore")

class deploy_environments:
    def __init__(self, logger, args, credentials, environment_name=None, environment_data=None):
        self._logger = logger
        self._args = args
        self._credentials = credentials
        self._environment_name = environment_name
        self._environment_data = environment_data
        self._servers = '' if self._args.servers is None else '--servers "{}"'.format(self._args.servers)

        self._bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

        self._show_output = self._credentials['execution_mode']['parallel'] == 'False'

        # Environment Variables
        self._script_path = sys._MEIPASS if self._bin else os.path.dirname(os.path.realpath(__file__))
        if self._environment_data is not None:
            # Deploy Path
            if self._environment_data['ssh']['enabled'] == 'True':
                self._bin_path = "{}/init".format(self._environment_data['ssh']['deploy_path']) if self._bin else "python3 {}/meteor.py".format(self._environment_data['ssh']['deploy_path'])
                self._ssh_logs_path = "{}/logs/{}".format(self._environment_data['ssh']['deploy_path'], self._args.uuid)
            else:
                self._bin_path = "{}/init".format(sys._MEIPASS) if self._bin else "python3 {}/meteor.py".format(os.path.dirname(os.path.realpath(__file__)))

    def validate(self):
        if self._credentials['execution_mode']['parallel'] == 'True':
            t = threading.current_thread()
        try:
            if self._show_output:
                environment_type = '[LOCAL]' if self._environment_data['ssh']['enabled'] == 'False' else '[SSH]'
                print(colored('{} Region: {}'.format(environment_type, self._environment_data['region']), attrs=['bold']))
            else:
                environment_type = '[LOCAL]' if self._environment_data['ssh']['enabled'] == 'False' else '[SSH]  '
                print(colored('--> {} Region \'{}\' Started...'.format(environment_type, self._environment_data['region']), 'yellow'))

            if self._environment_data['ssh']['enabled'] == "True":
                # same_version = self.check_version()
                # if same_version:
                #     if self._show_output:
                #         print(colored('- Region Updated.', 'green'))
                # else:
                #     if self._show_output:
                #         print(colored('- Region Outdated. Starting uploading the Meteor Engine...', 'red'))
                #     # Install Meteor in all SSH Regions
                #     self.prepare()
                # Setup User Execution Environment ('credentials.json', 'query_execution.py') & Check SQL Connection
                threads = []
                if not self._args.validate:
                    tsetup = threading.Thread(target=self.setup)
                    tsetup.start()
                    threads.append(tsetup)
                tcheck = threading.Thread(target=self.__check_sql_connection)
                tcheck.start()
                threads.append(tcheck)
                self.__wait_threads(threads)
                connection = tcheck.connection_results
            else:
                # Check SQL Connection
                connection = self.__check_sql_connection()

            if connection['success'] is True:
                print(colored('--> {} Region \'{}\' Finished.'.format(environment_type, self._environment_data['region']), 'green'))
            else:
                print(colored('--> {} Region \'{}\' Failed.'.format(environment_type, self._environment_data['region']), 'red'))

            if self._credentials['execution_mode']['parallel'] == 'True':
                t.progress = connection
            return connection['success']

        except Exception as e:
            if self._environment_data['ssh']['enabled'] == "True":
                # Handle SSH Error
                if self._credentials['execution_mode']['parallel'] == 'True':
                    print(colored("    [{}/SSH] {} ".format(self._environment_data['region'], self._environment_data['ssh']['hostname']), attrs=['bold']) + str(e))
                    t.progress = {'region': self._environment_data['region'], 'success': False, 'progress': [], 'error': str(e)}
                else:
                    print(colored("✘", 'red') + colored(" [{}] ".format(self._environment_data['ssh']['hostname']), attrs=['bold']) + str(e))

                print(colored('--> {} Region \'{}\' Failed.'.format(environment_type, self._environment_data['region']), 'red'))

        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

    def check_version(self):    
        # Get SSH Version
        ssh_version = self.__ssh("cat {}/version.txt".format(self._environment_data['ssh']['deploy_path']))['stdout']
        if len(ssh_version) == 0:
            return False
        else:
            ssh_version = ssh_version[0].replace('\n', '')

        # Get Local Version
        with open(self._script_path + '/version.txt') as file_content:
            local_version = file_content.read().replace('\n', '')

        # Compare Local & SSH Version
        if local_version != ssh_version:
            return False

        return True

    def generate_app_version(self):
        if not self._bin:
            version = ''
            files = os.listdir(self._script_path)
            for f in files:
                if not os.path.isdir(self._script_path + '/' + f) and not f.endswith('.pyc') and not f.startswith('.') and not f.endswith('.gz') and f not in ['version.txt', 'query_execution.py', 'credentials.json']:
                    with open("{0}/{1}".format(self._script_path, f), 'rb') as file_content:
                        file_hash = hashlib.sha512(file_content.read()).hexdigest()
                        version += file_hash
            with open('{}/version.txt'.format(self._script_path), 'w') as file_content:
                file_content.write(version)

    def prepare(self):
        if self._show_output:
            print('- Preparing Deploy...')
        self.__ssh("mkdir -p {0} && chmod 700 {0} && rm -rf {0}/*".format(self._environment_data['ssh']['deploy_path']))

        if self._show_output:
            print('- Creating Deploy...')
        
        if not self._bin:
            self.__local('cd {} && rm -rf meteor.tar.gz && tar -czvf meteor.tar.gz . --exclude "logs" --exclude "*.git*" --exclude "*.pyc" --exclude "web" --exclude "credentials.json" --exclude "query_execution.py"'.format(self._script_path), show_output=False)

        if self._show_output:
            print('- Uploading Deploy...')

        compressed_file_path = "{}/../meteor.tar.gz".format(self._script_path) if self._bin else "{}/meteor.tar.gz".format(self._script_path)
        self.__put(compressed_file_path, "{}/meteor.tar.gz".format(self._environment_data['ssh']['deploy_path']))

        if self._show_output:
            print("- Uncompressing Deploy...")
        self.__ssh("cd {} && tar -xvzf meteor.tar.gz -C . && rm -rf meteor.tar.gz".format(self._environment_data['ssh']['deploy_path']))

        if not self._bin:
            if self._show_output:
                print("- Installing Requirements...")
            self.__ssh('python3 -m pip install -r {}/requirements.txt --user'.format(self._environment_data['ssh']['deploy_path']))

    def setup(self, output=True):
        if self._show_output:
            print("- Setting Up New Execution...")
        self.__ssh('mkdir -p {}'.format(self._ssh_logs_path))
        tcred = threading.Thread(target=self.__setup_credentials)
        tquer = threading.Thread(target=self.__setup_query_execution)
        tcred.start()
        tquer.start()
        self.__wait_threads([tcred, tquer])
    
    def __setup_credentials(self):
        self.__put(self._args.logs_path + '/credentials.json', self._ssh_logs_path + '/credentials.json')
    
    def __setup_query_execution(self):
        self.__put(self._args.logs_path + '/query_execution.py', self._ssh_logs_path + '/query_execution.py')

    def start(self, shared_array=None, progress_array=None):
        try:           
            # Get Execution Plan Factor
            execution_plan_factor = '--execution_plan_factor "{}"'.format(self._args.execution_plan_factor) if self._args.execution_plan_factor is not None else ''

            # Parallel Execution
            if self._credentials['execution_mode']['parallel'] == "True":
                # SSH Execution
                if self._environment_data['ssh']['enabled'] == 'True':
                    # Start the Execution
                    if self._args.env_start_deploy:
                        deploy = self.__ssh('{0} --environment "{1}" {2} --env_id "{3}" --env_start_deploy --logs_path "{4}" {5} --uuid "{6}"'.format(self._bin_path, self._environment_name, self._servers, self._environment_data['region'], self._ssh_logs_path, execution_plan_factor, self._args.uuid), show_output=True, progress_array=progress_array)
                    else:
                        deploy = self.__ssh('{0} --environment "{1}" {2} --env_id "{3}" --logs_path "{4}" {5} --uuid "{6}"'.format(self._bin_path, self._environment_name, self._servers, self._environment_data['region'], self._ssh_logs_path, execution_plan_factor, self._args.uuid), show_output=True, progress_array=progress_array)
                # Local Execution
                else:
                    if self._args.env_start_deploy:
                        deploy = self.__local('{0} --environment "{1}" {2} --env_id "{3}" --env_start_deploy --logs_path "{4}" {5} --uuid "{6}"'.format(self._bin_path, self._environment_name, self._servers, self._environment_data['region'], self._args.logs_path, execution_plan_factor, self._args.uuid), show_output=True, progress_array=progress_array)
                    else:
                        deploy = self.__local('{0} --environment "{1}" {2} --env_id "{3}" --logs_path "{4}" {5} --uuid "{6}"'.format(self._bin_path, self._environment_name, self._servers, self._environment_data['region'], self._args.logs_path, execution_plan_factor, self._args.uuid), show_output=True, progress_array=progress_array)

                # Check for Execution Error
                if len(deploy['stderr']) > 0:
                    # Parse stderr
                    stderr_parsed = str(deploy['stderr'].encode('utf-8')).split("Traceback (most recent call last):\n")
                    if len(stderr_parsed) > 1:
                        stderr_parsed = "Traceback (most recent call last):\n" + stderr_parsed[1]
                        if stderr_parsed.splitlines()[-1].startswith('Process Process-'):
                            stderr_parsed = stderr_parsed.rsplit("\n",2)[0]
                    else:
                        stderr_parsed = deploy['stderr']

                    shared_array.append({ "region": self._environment_data['region'], "success": False, "error": stderr_parsed })
                else:
                    shared_array.append({ "region": self._environment_data['region'], "success": True })

            # Sequential Execution
            else:
                # SSH Execution
                if self._environment_data['ssh']['enabled'] == 'True':
                    # Start the Execution
                    if self._args.env_start_deploy:
                        stderr = self.__ssh('{0} --environment "{1}" {2} --env_id "{3}" --env_start_deploy --logs_path "{4}" --uuid "{5}"'.format(self._bin_path, self._environment_name, self._servers, self._environment_data['region'], self._ssh_logs_path, self._args.uuid), show_output=True)['stderr']
                    else:
                        stderr = self.__ssh('{0} --environment "{1}" {2} --env_id "{3}" --logs_path "{4}" --uuid "{5}"'.format(self._bin_path, self._environment_name, self._servers, self._environment_data['region'], self._ssh_logs_path, self._args.uuid), show_output=True)['stderr']
                # Local Execution
                else:
                    if self._args.env_start_deploy:
                        stderr = self.__local('{0} --environment "{1}" {2} --env_id "{3}" --env_start_deploy --logs_path "{4}" --uuid "{5}"'.format(self._bin_path, self._environment_name, self._servers, self._environment_data['region'], self._args.logs_path, self._args.uuid), show_output=True)['stderr']
                    else:
                        stderr = self.__local('{0} --environment "{1}" {2} --env_id "{3}" --logs_path "{4}" --uuid "{5}"'.format(self._bin_path, self._environment_name, self._servers, self._environment_data['region'], self._args.logs_path, self._args.uuid), show_output=True)['stderr']

                # Check for Execution Error
                if len(stderr) > 0:
                    # Remove last '\n' character
                    raise Exception(stderr[:-1])

        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

    def compress_logs(self):
        output = self.__ssh('{0} --environment "{1}" {2} --env_id "{3}" --env_compress --logs_path "{4}" --uuid "{5}"'.format(self._bin_path, self._environment_name, self._servers, self._environment_data['region'], self._ssh_logs_path, self._args.uuid))

        if self._credentials['execution_mode']['parallel'] == 'True' and len(output['stderr']) > 0:
            t = threading.current_thread()
            t.error.append(output['stderr'])

    def get_logs(self):
        try:
            if self._environment_data['ssh']['enabled'] == 'True':
                remote_path = "{0}/logs/{1}/execution/{2}.tar.gz".format(self._environment_data['ssh']['deploy_path'], self._args.uuid, self._environment_data['region'])
                local_path = "{0}/execution/{1}".format(self._args.logs_path, self._environment_data['region'])

                # 1. Download Compressed Logs
                status = self.__get(remote_path, local_path + '.tar.gz')

                if status:
                    # 2. Uncompress Downloaded Logs
                    with tarfile.open(local_path + '.tar.gz') as tar:
                        tar.extractall(path=self._args.logs_path + '/execution')
                    # 3. Delete Downloaded Compressed Logs
                    os.remove(local_path + '.tar.gz')
        except Exception:
            if self._credentials['execution_mode']['parallel'] != 'True':
                self._logger.error(colored("--> Error Downloading Logs:\n{}".format(traceback.format_exc()), 'red'))
                raise
            else:
                t = threading.current_thread()
                t.error.append(traceback.format_exc())

    def clean_remote(self, remote=True):
        if remote:
            # Clean Remote Execution Logs
            environment_logs = "{}/logs/{}/".format(self._environment_data['ssh']['deploy_path'], self._args.uuid)
            output = self.__ssh('rm -rf {0}'.format(environment_logs))

            if len(output['stderr']) > 0 and self._credentials['execution_mode']['parallel'] != 'True':
                t = threading.current_thread()
                t.error = output['stderr']

    def clean_local(self):
        # Delete Uncompressed Deployment Folder
        if os.path.exists(self._args.logs_path):
            if os.path.isdir(self._args.logs_path):
                shutil.rmtree(self._args.logs_path)

        # Delete 'meteor.tar.gz'
        self.__local('rm -rf {}/meteor.tar.gz'.format(self._script_path), show_output=False)

    def __check_sql_connection(self):
        connection_results = {'region': self._environment_data['region'], 'success': False, 'progress': []}
        connection_succeeded = True          

        if self._credentials['execution_mode']['parallel'] == "True":
            thread = threading.current_thread()
            try:
                threads = []
                for server in self._environment_data['sql']:
                    t = threading.Thread(target=self.__check_sql_connection_logic, args=(server,))
                    threads.append(t)
                    t.start()

                # Wait threads
                self.__wait_threads(threads)
                # Get values
                for t in threads:
                    connection_succeeded &= t.progress['success']
                    if t.progress['success'] is False:
                        print(colored("    [{}/SQL] {} ".format(self._environment_data['region'], t.progress['sql']), attrs=['bold']) + t.progress['error'])
                        connection_results['progress'].append({'server': t.progress['sql'], 'error': t.progress['error'].replace('"', '\\"')})
                # Set return value
                connection_results['success'] = connection_succeeded
                thread.connection_results = connection_results
            except (Exception,KeyboardInterrupt):
                self.__stop_threads(threads)
                raise
        else:
            print("- Checking SQL Connections...")
            for server in self._environment_data['sql']:
                connection_succeeded &= self.__check_sql_connection_logic(server)
            connection_results['success'] = connection_succeeded
        return connection_results

    def __wait_threads(self, threads):
        for t in threads:
            t.join()

    def __stop_threads(self, threads):
        for t in threads:
            t.alive = False
        self.__wait_threads(threads)  

    def __check_sql_connection_logic(self, server):
        if self._credentials['execution_mode']['parallel'] == 'True':
            t = threading.current_thread()

        attempts = 5
        error = None

        for i in range(attempts):
            try:
                region = self._environment_data
                if region['ssh']['enabled'] == "True":
                    ssh_pkey = paramiko.RSAKey.from_private_key_file(region['ssh']['key'])
                    with sshtunnel.SSHTunnelForwarder((region['ssh']['hostname'], int(region['ssh']['port'])), ssh_username=region['ssh']['username'], ssh_password=region['ssh']['password'], ssh_pkey=ssh_pkey, remote_bind_address=(server['hostname'], int(server['port']))) as tunnel:
                        conn = pymysql.connect(host='127.0.0.1', port=tunnel.local_bind_port, user=server['username'], passwd=server['password'])
                        conn.close()
                else:
                    conn = pymysql.connect(host=server['hostname'], port=server['port'], user=server['username'], passwd=server['password'])
                if self._show_output:
                    print(colored("✔", 'green') + colored(" [{}]".format(server['name']), attrs=['bold']) + " Connection Succeeded")
                else:
                    t.progress = {"region": region['region'], "success": True, "sql": server['name']}
                return True
            except Exception as e:
                error = e
                time.sleep(1)

        if self._show_output:
            print(colored("✘", 'red') + colored(" [{}] ".format(server['name']), attrs=['bold']) + str(error).replace('\n',''))
        else:
            t.progress = {"region": region['region'], "success": False, "sql": server['name'], "error": str(error).replace('\n','')}
        return False

    def check_processes(self):
        # Check Processes Currently Executing
        attempts = 5

        for i in range(attempts):
            command = "ps -U $USER -u $USER u | grep \"" + str(self._args.uuid) + "\" | grep -v grep | awk '{print $2}' | wc -l"
            
            if self._environment_data['ssh']['enabled'] == 'False':
                count = int(self.__local(command)['stdout'][0])
                print("-- [Attempt {}/{}] Remaining Processes: {}".format(i+1, attempts, int(count)))
            else:
                count = int(self.__ssh(command)['stdout'][0])
                print("-- [Attempt {}/{}] Remaining Processes: {}".format(i+1, attempts, int(count)))

            if int(count) == 0:
                break
            time.sleep(2)

    def sigint(self):
        command = "ps -U $USER -u $USER u | grep \"" + str(self._args.uuid) + "\" | grep -v grep | awk '{print $2}' | xargs kill -2"

        if self._environment_data['ssh']['enabled'] == 'False':
            self.__local(command)
        else:
            self.__ssh(command)

    def sigkill(self):
        command = "ps -U $USER -u $USER u | grep '" + str(self._args.logs_path) + "' | grep '--env_id'  | grep -v grep | awk '{print $2}' | xargs kill -9 2> /dev/null"
        if self._environment_data and self._environment_data['ssh']['enabled'] == 'True':
            self.__ssh(command)
        else:
            self.__local(command)

    ################
    # Core Methods #
    ################
    def __local(self, command, show_output=False, progress_array=None):
        # Paramiko Execute Local Command
        client = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Show Output 
        if show_output:
            for line in client.stdout:
                if progress_array is None:
                    print(self.__decode(line.rstrip()))
                else:
                    # print(self.__decode(line.rstrip()))
                    progress_array.append(self.__decode(line))

        # Return Execution Output
        return { "stdout": [self.__decode(i) for i in client.stdout.readlines()], "stderr": ''.join(str(v) for v in client.stderr.readlines()) }

    def __ssh(self, command, show_output=False, progress_array=None):
        try:
            # Supress Errors Output
            sys_stderr = sys.stderr
            sys.stderr = open('/dev/null', 'w')

            # Init Paramiko SSH Connection
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(hostname=self._environment_data['ssh']['hostname'], port=int(self._environment_data['ssh']['port']), username=self._environment_data['ssh']['username'], password=self._environment_data['ssh']['password'], key_filename=self._environment_data['ssh']['key'], timeout=10)

            # Show Errors Output Again
            sys.stderr = sys_stderr

            # Paramiko Execute Command
            stdin, stdout, stderr = client.exec_command(command, get_pty=False)
            stdin.close()

            if show_output:
                for line in stdout:
                    if progress_array is None:
                        print(line.rstrip())
                    else:
                        # print(self.__decode(line.rstrip()))
                        progress_array.append(self.__decode(line))

            # Return Execution Output
            return { "stdout": [self.__decode(i) for i in stdout.readlines()], "stderr": ''.join(stderr.readlines()) }

        except socket.error as e:
            raise Exception("Connection Timeout. Can't establish a SSH connection.")

        finally:
            # Paramiko Close Connection
            if client.get_transport() is not None and client.get_transport().is_active():
                client.close()

    def __get(self, remote_path, local_path):
        try:
            # Supress Errors Output
            sys_stderr = sys.stderr
            sys.stderr = open('/dev/null', 'w')

            # Init Paramiko Connection
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(hostname=self._environment_data['ssh']['hostname'], port=int(self._environment_data['ssh']['port']), username=self._environment_data['ssh']['username'], password=self._environment_data['ssh']['password'], key_filename=self._environment_data['ssh']['key'], timeout=10)

            # Show Errors Output Again
            sys.stderr = sys_stderr

            # Open sftp connection
            sftp = client.open_sftp()

            # Check if file exists (ls)
            sftp.stat(remote_path)
            
            # Download File
            sftp.get(remote_path, local_path)
            return True

        except IOError:
            return False
        finally:
            sftp.close()

    def __put(self, local_path, remote_path):
        try:
            # Init Paramiko Connection
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(hostname=self._environment_data['ssh']['hostname'], port=int(self._environment_data['ssh']['port']), username=self._environment_data['ssh']['username'], password=self._environment_data['ssh']['password'], key_filename=self._environment_data['ssh']['key'], timeout=10)

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