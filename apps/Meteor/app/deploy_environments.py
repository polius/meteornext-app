#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import multiprocessing
import signal
import sys
import time
import paramiko
import traceback
import shutil
import tarfile
import hashlib
from multiprocessing.managers import SyncManager
from colors import colored


class deploy_environments:
    def __init__(self, logger, args, credentials, execution_name=None, ENV_NAME=None, ENV_DATA=None, uuid=None):
        self._logger = logger
        self._args = args
        self._credentials = credentials
        self._SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
        self._EXECUTION_NAME = execution_name
        self._ENV_NAME = ENV_NAME
        self._ENV_DATA = ENV_DATA
        self._UUID = uuid
        self._COMPRESSED_FILE_NAME = 'METEOR.tar.gz'
        self._servers = '' if self._args.servers is None else '--servers "{}"'.format(self._args.servers)

        # Setup the Execution Logs Path
        self._LOGS_PATH = self._args.logs_path if self._args.logs_path.endswith('/') else self._args.logs_path + '/'
        self._LOCAL_EXECUTION_LOGS_PATH = "{}{}/execution".format(self._LOGS_PATH, self._EXECUTION_NAME)

        # Environment Variables
        if self._ENV_DATA is not None:
            # Deploy Path
            if self._ENV_DATA['ssh']['enabled'] == 'True':
                self._DEPLOY_PATH = self._ENV_DATA['ssh']['deploy_path'] + 'meteor/'
            else:
                self._DEPLOY_PATH = self._SCRIPT_PATH + '/'

            # Remote Execution Logs Path
            self._REMOTE_EXECUTION_LOGS_PATH = "{}logs/{}/execution".format(self._DEPLOY_PATH, execution_name)

    def validate(self, output=True, shared_array=None):
        try:
            if output:
                environment_type = '[LOCAL]' if self._ENV_DATA['ssh']['enabled'] == 'False' else '[SSH]'
                print(colored('{} Region: {}'.format(environment_type, self._ENV_DATA['region']), attrs=['bold']))
            else:
                environment_type = '[LOCAL]' if self._ENV_DATA['ssh']['enabled'] == 'False' else '[SSH]  '
                print(colored('--> {} Region \'{}\' Started...'.format(environment_type, self._ENV_DATA['region']), 'yellow'))

            if self._ENV_DATA['ssh']['enabled'] == "True":
                same_version = self.check_version(output)
                if same_version:
                    if output:
                        print(colored('- Region Updated.', 'green'))
                else:
                    if output:
                        print(colored('- Region Outdated. Starting uploading the Meteor Engine...', 'red'))
                    # Install Meteor in all SSH Regions
                    self.prepare(output)
                # Setup User Execution Environment ('credentials.json', 'query_execution.py')
                self.setup(output)

            # Check SQL Connection of the Environment [True: All SQL Connections Succeeded | False: Some SQL Connections Failed]
            connection = self.__check_sql_connection(output)

            if connection['success'] is True:
                print(colored('--> {} Region \'{}\' Finished.'.format(environment_type, self._ENV_DATA['region']), 'green'))
            else:
                print(colored('--> {} Region \'{}\' Failed.'.format(environment_type, self._ENV_DATA['region']), 'red'))

            if shared_array is not None:
                shared_array.append(connection)

            return connection['success']

        except Exception as e:
            if self._ENV_DATA['ssh']['enabled'] == "True":
                # Handle SSH Error
                if self._credentials['execution_mode']['parallel'] == 'True':
                    print(colored("    [{}/SSH] {} ".format(self._ENV_DATA['region'], self._ENV_DATA['ssh']['hostname']), attrs=['bold']) + str(e))
                else:
                    print(colored("✘", 'red') + colored(" [{}] ".format(self._ENV_DATA['ssh']['hostname']), attrs=['bold']) + str(e))

                print(colored('--> {} Region \'{}\' Failed.'.format(environment_type, self._ENV_DATA['region']), 'red'))
            raise
        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

    def check_version(self, output=True):    
        # Get SSH Version
        ssh_version = self.__ssh("cat {}version.txt".format(self._DEPLOY_PATH))['stdout']
        if len(ssh_version) == 0:
            return False
        else:
            ssh_version = ssh_version[0].replace('\n', '')

        # Get Local Version
        with open(self._SCRIPT_PATH + '/version.txt') as file_content:
            local_version = file_content.read().replace('\n', '')

        # Compare Local & SSH Version
        if local_version != ssh_version:
            return False

        return True

    def generate_app_version(self):
        version = ''
        files = os.listdir(self._SCRIPT_PATH)
        for f in files:
            if not os.path.isdir(self._SCRIPT_PATH + '/' + f) and not f.endswith('.pyc') and not f.startswith('.') and not f.endswith('.gz') and f not in ['version.txt', 'query_execution.py', 'credentials.json']:
                with open("{0}/{1}".format(self._SCRIPT_PATH, f), 'rb') as file_content:
                    file_hash = hashlib.sha512(file_content.read()).hexdigest()
                    version += file_hash
        return version

    def prepare(self, output=True):
        if output:
            print('- Preparing Deploy...')
        self.__ssh("mkdir -p {0} && chmod 700 {0} && rm -rf {0}*".format(self._DEPLOY_PATH))

        if output:
            print('- Creating Deploy...')
        self.__local('rm -rf "{0}" && tar -czvf "{0}" . --exclude "logs" --exclude "*.git*" --exclude "*.pyc" --exclude "web" --exclude "credentials.json" --exclude "query_execution.py"'.format(self._COMPRESSED_FILE_NAME), show_output=False)

        if output:
            print('- Uploading Deploy...')
        self.__put(self._SCRIPT_PATH + '/' + self._COMPRESSED_FILE_NAME, self._DEPLOY_PATH + self._COMPRESSED_FILE_NAME)

        if output:
            print("- Uncompressing Deploy...")
        self.__ssh("tar -xvzf {0}{1} -C {0} && rm -rf {0}{1}".format(self._DEPLOY_PATH, self._COMPRESSED_FILE_NAME))

        if output:
            print("- Installing Requirements...")
        self.__ssh('pip install -r {}meteor/requirements.txt --user'.format(self._ENV_DATA['ssh']['deploy_path']))

    def setup(self, output=True):
        if output:
            print("- Setting Up New Execution...")

        logs_path = "{}logs/{}/".format(self._DEPLOY_PATH, self._EXECUTION_NAME)
        self.__ssh('mkdir -p {}'.format(logs_path))
        self.__put(self._SCRIPT_PATH + '/credentials.json', logs_path + 'credentials.json')
        self.__put(self._SCRIPT_PATH + '/query_execution.py', logs_path + 'query_execution.py')

    def start(self, shared_array=None, progress_array=None):
        try:
            # Parallel Execution
            if self._credentials['execution_mode']['parallel'] == "True":
                # SSH Execution
                if self._ENV_DATA['ssh']['enabled'] == 'True':
                    # Start the Execution
                    if self._args.env_start_deploy:
                        deploy = self.__ssh('cd "{0}" && python -u meteor.py --environment "{1}" {2} --env_id "{3}" --env_start_deploy --execution_name "{4}" --uuid "{5}"'.format(self._DEPLOY_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], self._EXECUTION_NAME, self._UUID), show_output=True, progress_array=progress_array)
                    else:
                        deploy = self.__ssh('cd "{0}" && python -u meteor.py --environment "{1}" {2} --env_id "{3}" --execution_name "{4}" --uuid "{5}"'.format(self._DEPLOY_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], self._EXECUTION_NAME, self._UUID), show_output=True, progress_array=progress_array)
                # Local Execution
                else:
                    if self._args.env_start_deploy:
                        deploy = self.__local('python -u {0}/meteor.py --environment "{1}" {2} --env_id "{3}" --env_start_deploy --execution_name "{4}" --logs_path "{5}" --uuid "{6}"'.format(self._SCRIPT_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], self._EXECUTION_NAME, self._args.logs_path, self._UUID), show_output=True, progress_array=progress_array)
                    else:
                        deploy = self.__local('python -u {0}/meteor.py --environment "{1}" {2} --env_id "{3}" --execution_name "{4}" --logs_path "{5}" --uuid "{6}"'.format(self._SCRIPT_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], self._EXECUTION_NAME, self._args.logs_path, self._UUID), show_output=True, progress_array=progress_array)

                # Check for Execution Error
                if len(deploy['stderr']) > 0:
                    # Parse stderr
                    stderr_parsed = str(deploy['stderr']).split("Traceback (most recent call last):\n")
                    if len(stderr_parsed) > 1:
                        stderr_parsed = "Traceback (most recent call last):\n" + stderr_parsed[1]
                        if stderr_parsed.splitlines()[-1].startswith('Process Process-'):
                            stderr_parsed = stderr_parsed.rsplit("\n",2)[0]
                    else:
                        stderr_parsed = deploy['stderr']

                    shared_array.append({ "region": self._ENV_DATA['region'], "success": False, "error": stderr_parsed })
                else:
                    shared_array.append({ "region": self._ENV_DATA['region'], "success": True })

            # Sequential Execution
            else:
                # SSH Execution
                if self._ENV_DATA['ssh']['enabled'] == 'True':
                    # Start the Execution
                    if self._args.env_start_deploy:
                        stderr = self.__ssh('cd "{0}" && python meteor.py --environment "{1}" {2} --env_id "{3}" --env_start_deploy --execution_name "{4}"'.format(self._DEPLOY_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], self._EXECUTION_NAME), show_output=True)['stderr']
                    else:
                        stderr = self.__ssh('cd "{0}" && python meteor.py --environment "{1}" {2} --env_id "{3}" --execution_name "{4}"'.format(self._DEPLOY_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], self._EXECUTION_NAME), show_output=True)['stderr']
                # Local Execution
                else:
                    if self._args.env_start_deploy:
                        stderr = self.__local('python {0}/meteor.py --environment "{1}" {2} --env_id "{3}" --env_start_deploy --execution_name "{4}" --logs_path "{5}"'.format(self._SCRIPT_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], self._EXECUTION_NAME, self._args.logs_path), show_output=True)['stderr']
                    else:
                        stderr = self.__local('python {0}/meteor.py --environment "{1}" {2} --env_id "{3}" --execution_name "{4}" --logs_path "{5}"'.format(self._SCRIPT_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], self._EXECUTION_NAME, self._args.logs_path), show_output=True)['stderr']

                # Check for Execution Error
                if len(stderr) > 0:
                    # Remove last '\n' character
                    raise Exception(stderr[:-1])

        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

    def compress_logs(self, shared_array=None):
        try:
            output = self.__ssh('cd "{0}" && python meteor.py --environment "{1}" {2} --env_id "{3}" --env_compress --execution_name "{4}"'.format(self._DEPLOY_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], self._EXECUTION_NAME))

            if len(output['stderr']) > 0:
                shared_array.append(output['stderr'])

        except (KeyboardInterrupt):
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

    def get_logs(self, shared_array=None):
        try:
            if self._ENV_DATA['ssh']['enabled'] == 'True':
                remote_path = "{0}/{1}.tar.gz".format(self._REMOTE_EXECUTION_LOGS_PATH, self._ENV_DATA['region'])
                local_path = "{0}/{1}".format(self._LOCAL_EXECUTION_LOGS_PATH, self._ENV_DATA['region'])

                # 1. Download Compressed Logs
                status = self.__get(remote_path, local_path + '.tar.gz')

                if status:
                    # 2. Uncompress Downloaded Logs
                    with tarfile.open(local_path + '.tar.gz') as tar:
                        tar.extractall(path=self._LOCAL_EXECUTION_LOGS_PATH)

                    # 3. Delete Downloaded Compressed Logs
                    os.remove(local_path + '.tar.gz')

        except Exception:
            if self._credentials['execution_mode']['parallel'] != 'True':
                self._logger.error(colored("--> Error Downloading Logs:\n{}".format(traceback.format_exc()), 'red'))
                raise
            else:
                shared_array.append(traceback.format_exc())
        
        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

    def clean_remote(self, shared_array=None):
        environment_logs = "{}logs/{}/".format(self._DEPLOY_PATH, self._EXECUTION_NAME)
        output = self.__ssh('rm -rf {0}'.format(environment_logs))

        if len(output['stderr']) > 0:
            shared_array.append(output['stderr'])

    def clean_local(self):
        # Delete Uncompressed Deployment Folder
        if os.path.exists(self._LOGS_PATH + self._EXECUTION_NAME):
            if os.path.isdir(self._LOGS_PATH + self._EXECUTION_NAME):
                shutil.rmtree(self._LOGS_PATH + self._EXECUTION_NAME)

        # Delete 'METEOR.tar.gz'
        self.__local('rm -rf {0}'.format(self._COMPRESSED_FILE_NAME), show_output=False)

    # Handle SIGINT from SyncManager object
    def mgr_sig_handler(self, signal, frame):
        pass

    # Initilizer for SyncManager
    def __mgr_init(self):
        signal.signal(signal.SIGINT, self.mgr_sig_handler)

    def __check_sql_connection(self, output):
        connection_results = {'region': self._ENV_DATA['region'], 'success': False, 'progress': []}
        connection_succeeded = True

        if output:
            print("- Checking SQL Connections...")

        if self._credentials['execution_mode']['parallel'] == "True":
            # Init SyncManager
            manager = SyncManager()
            manager.start(self.__mgr_init)
            shared_array = manager.list()
            processes = []

            try:
                for sql in self._ENV_DATA['sql']:
                    p = multiprocessing.Process(target=self.__check_sql_connection_logic, args=(sql, output, shared_array))
                    p.start()
                    processes.append(p)

                for process in processes:
                    process.join()

                progress = []
                for data in shared_array:
                    connection_succeeded &= data['success']
                    if data['success'] is False:
                        print(colored("    [{}/SQL] {} ".format(self._ENV_DATA['region'], data['sql']), attrs=['bold']) + data['error'])
                        connection_results['progress'].append({'server': data['sql'], 'error': data['error'].replace('"', '\\"')})

            except KeyboardInterrupt:
                for process in processes:
                    process.join()
                raise
        else:
            for sql in self._ENV_DATA['sql']:
                connection_succeeded &= self.__check_sql_connection_logic(sql, output)

        connection_results['success'] = connection_succeeded
        return connection_results

    def __check_sql_connection_logic(self, sql, output, shared_array=None):
        try:
            if self._ENV_DATA['ssh']['enabled'] == 'True':
                command = 'cd "{0}" && python meteor.py --environment "{1}" {2} --env_id "{3}" --env_check_sql "{4}" --execution_name "{5}"'.format(self._DEPLOY_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], sql['name'], self._EXECUTION_NAME)
                result = self.__ssh(command)['stdout']
            else:
                result = self.__local('cd "{0}" && python meteor.py --environment "{1}" {2} --env_id "{3}" --env_check_sql "{4}" --execution_name "{5}" --logs_path "{6}"'.format(self._SCRIPT_PATH, self._ENV_NAME, self._servers, self._ENV_DATA['region'], sql['name'], self._EXECUTION_NAME, self._args.logs_path), show_output=False)['stdout']
            
            if len(result) == 0:
                if output:
                    print(colored("✔", 'green') + colored(" [{}]".format(sql['name']), attrs=['bold']) + " Connection Succeeded")
                if shared_array is not None:
                    shared_array.append({"region": self._ENV_DATA['region'], "success": True, "sql": sql['name']})
                return True
            else:
                result = result[0] if type(result) is list else result
                if output:
                    self._logger.error(colored("✘", 'red') + colored(" [{}] ".format(sql['name']), attrs=['bold']) + str(result.replace('\n','')))
                if shared_array is not None:
                    shared_array.append({"region": self._ENV_DATA['region'], "success": False, "sql": sql['name'], "error": result.replace('\n','')})
                return False

        except KeyboardInterrupt:
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

        except Exception:      
            if self._credentials['execution_mode']['parallel'] != 'True':
                raise

    def sigint(self):
        command = "ps -U $USER -u $USER u | grep \"" + str(self._UUID) + "\" | grep -v grep | awk '{print $2}' | xargs kill -2"

        if self._ENV_DATA['ssh']['enabled'] == 'False':
            self.__local(command)
        else:
            self.__ssh(command)
    
    def check_processes(self):
        # Check Processes Currently Executing
        attempts = 99

        for i in range(attempts+1):
            command = "ps -U $USER -u $USER u | grep \"" + str(self._UUID) + "\" | grep -v grep | awk '{print $2}' | wc -l"
            
            if self._ENV_DATA['ssh']['enabled'] == 'False':
                count = int(self.__local(command)['stdout'][0])
                print("-- [Attempt {}/{}] Remaining Processes: {}".format(i+1, attempts, int(count)))
            else:
                count = int(self.__ssh(command)['stdout'][0])
                print("-- [Attempt {}/{}] Remaining Processes: {}".format(i+1, attempts, int(count)))

            if int(count) == 0:
                break
            time.sleep(10)


    def sigkill(self):
        command = "ps -U $USER -u $USER u | grep \"" + str(self._UUID) + "\" | grep -v grep | awk '{print $2}' | xargs kill -9 2> /dev/null"
        if self._ENV_DATA['ssh']['enabled'] == 'False':
            self.__local(command)
        else:
            self.__ssh(command)

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
                    print(line.rstrip())
                else:
                    progress_array.append(line)

        # Return Execution Output
        return { "stdout": client.stdout.readlines(), "stderr": ''.join(client.stderr.readlines()) }

    def __ssh(self, command, show_output=False, progress_array=None):
        try:
            # Supress Errors Output
            sys_stderr = sys.stderr
            sys.stderr = open('/dev/null', 'w')

            # Init Paramiko SSH Connection
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(self._ENV_DATA['ssh']['hostname'], port=22, username=self._ENV_DATA['ssh']['username'], password=self._ENV_DATA['ssh']['password'], key_filename=self._ENV_DATA['ssh']['key'])

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
                        progress_array.append(line)

            # Return Execution Output
            return { "stdout": stdout.readlines(), "stderr": ''.join(stderr.readlines()) }

        finally:
            # Paramiko Close Connection
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
            client.connect(self._ENV_DATA['ssh']['hostname'], port=22, username=self._ENV_DATA['ssh']['username'], password=self._ENV_DATA['ssh']['password'], key_filename=self._ENV_DATA['ssh']['key'])
            
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
            client.connect(self._ENV_DATA['ssh']['hostname'], port=22, username=self._ENV_DATA['ssh']['username'], password=self._ENV_DATA['ssh']['password'], key_filename=self._ENV_DATA['ssh']['key'])

            # Open sftp connection
            sftp = client.open_sftp()

            # Upload File
            sftp.put(local_path, remote_path)

        finally:
            if 'sftp' in locals():
                sftp.close()
