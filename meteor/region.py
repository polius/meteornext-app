import os
import sys
import json
import time
import paramiko
import threading
import subprocess
import shutil
import tarfile

class Region:
    def __init__(self, args, region):
        self._args = args
        self._region = region
        self._bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._local_path = os.path.dirname(os.path.realpath(__file__)) if not self._bin else sys._MEIPASS
        self._remote_path = ".meteor" if region['ssh']['enabled'] else None
        # Get UUID from path
        self._uuid = self._args.path[self._args.path.rfind('/')+1:]

    def check_version(self):
        # Get SSH Version
        ssh_version = self.__ssh("cat {}/bin/version.txt".format(self._remote_path))
        if len(ssh_version) == 0:
            return False

        # Get Local Version
        with open("{}/version.txt".format(self._local_path)) as file_content:
            local_version = file_content.read()

        # Compare Local & SSH Version
        return local_version == ssh_version

    def upload_binary(self):
        # Upload Binary
        if self._bin:
            self.__ssh("rm -rf {0}/bin && mkdir -p {0}/bin".format(self._remote_path))
            self.__put("{}.tar.gz".format(self._local_path), ".meteor/bin/meteor.tar.gz")
            self.__ssh("tar -xvzf {0}/bin/meteor.tar.gz -C {0}/bin && rm -rf {0}/bin/meteor.tar.gz".format(self._remote_path))
        else:
            # Compress Meteor files
            shutil.make_archive(self._local_path, 'gztar', self._local_path)
            shutil.move(f"{self._local_path}.tar.gz", f"{self._local_path}/../server/apps/meteor.tar.gz")
            # Upload Meteor
            self.__ssh(f"rm -rf {self._remote_path}/bin && mkdir -p {self._remote_path}/bin")
            self.__put(f"{self._local_path}/../server/apps/meteor.tar.gz", ".meteor/bin/meteor.tar.gz")
            self.__ssh("tar -xvzf {0}/bin/meteor.tar.gz -C {0}/bin && rm -rf {0}/bin/meteor.tar.gz".format(self._remote_path))

    def get_logs(self):
        # 1. Compress Logs
        binary_path = "{}/bin/init".format(self._remote_path) if self._bin else "python3 {}/bin/meteor.py".format(self._remote_path)
        self.__ssh('{} --path "{}/deployments/{}" --region "{}" --compress'.format(binary_path, self._remote_path, self._uuid, self._region['name']))
        # 2. Download Compressed Logs
        remote_path = ".meteor/deployments/{}/execution/{}.tar.gz".format(self._uuid, self._region['name'])
        local_path = "{}/execution/{}.tar.gz".format(self._args.path, self._region['name'])
        status = self.__get(remote_path, local_path)

        if status:
            # 3. Uncompress Downloaded Logs
            with tarfile.open(local_path) as tar:
                tar.extractall(path="{}/execution".format(self._args.path))

    def get_progress(self):
        current_thread = threading.current_thread()

        if self._region['ssh']['enabled']:
            progress = self.__ssh("cat {}/deployments/{}/execution/{}/progress.json 2>/dev/null".format(self._remote_path, self._uuid, self._region['name']))
        else:
            progress = self.__local("cat {}/execution/{}/progress.json 2>/dev/null".format(self._args.path, self._region['name']))
        current_thread.progress = json.loads(progress) if len(progress) > 0 else {}

    def clean(self):
        current_thread = threading.current_thread()
        try:
            self.__ssh("rm -rf {}/deployments/{}".format(self._remote_path, self._uuid), retry=False)
            current_thread.progress = {'region': self._region['name'], 'success': True}
        except Exception as e:
            current_thread.progress = {'region': self._region['name'], 'success': False, 'error': str(e)}

    def check_processes(self):
        # Check Processes Currently Executing
        command = "ps -U $USER -u $USER u | grep '{}' | grep '\-\-region' | grep -v grep | awk '{{print $2}}' | wc -l".format(self._uuid)
        count = self.__ssh(command) if self._region['ssh']['enabled'] else self.__local(command)
        return int(count)

    def sigint(self):
        command = "ps -U $USER -u $USER u | grep '{}' | grep '\--region' | grep -v grep | awk '{{print $2}}' | xargs kill -2 2> /dev/null".format(self._uuid)
        if self._region['ssh']['enabled']:
            self.__ssh(command, self._args.path + '/deployments/' + self._region['name'])
        else:
            self.__local(command)

    def sigkill(self):
        command = "ps -U $USER -u $USER u | grep '{}' | grep '\--region' | grep -v grep | awk '{{print $2}}' | xargs kill -9 2> /dev/null".format(self._uuid)
        if self._region['ssh']['enabled']:
            self.__ssh(command)
        else:
            self.__local(command)

    ##########
    # REMOTE #
    ##########
    def deploy(self):
        # Deploy new execution
        mode = 'validate' if self._args.validate else 'test' if self._args.test else 'deploy'
        
        if self._region['ssh']['enabled']:
            binary_path = "{}/bin/init".format(self._remote_path) if self._bin else "python3 {}/bin/meteor.py".format(self._remote_path)

            # Upload execution
            self.__ssh('mkdir -p {}/deployments/{}'.format(self._remote_path, self._uuid))
            self.__put("{}/config.json".format(self._args.path), ".meteor/deployments/{}/config.json".format(self._uuid))
            self.__put("{}/blueprint.py".format(self._args.path), ".meteor/deployments/{}/blueprint.py".format(self._uuid))
            # Start execution
            self.__ssh('{} --path "{}/deployments/{}" --{} --region "{}"'.format(binary_path, self._remote_path, self._uuid, mode, self._region['name']), self._args.path + '/deployments/' + self._region['name'])
        else:
            binary_path = "{}/init".format(self._local_path) if self._bin else "python3 {}/meteor.py".format(self._local_path)
            # Start execution
            self.__local('{} --path "{}" --{} --region "{}"'.format(binary_path, self._args.path, mode, self._region['name']))

        # Wait deploy to finish
        while self.check_processes() > 0:
            time.sleep(5)

    def compress_logs(self):
        compressed_dir = "{}/execution/{}".format(self._args.path, self._region['name'])
        compressed_path = "{}/execution".format(self._args.path)
        shutil.make_archive(compressed_dir, 'gztar', compressed_path)

    ################
    # Core Methods #
    ################
    def __local(self, command):
        # Paramiko Execute Local Command
        client = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Get stdout
        stdout = client.stdout.readlines()

        # Return Execution Output
        return stdout[0] if len(stdout) > 0 else ''

    def __ssh(self, command, path=None, retry=True):
        retries = 6 if retry else 1
        for i in range(retries):
            try:
                # Supress Errors Output
                sys_stderr = sys.stderr
                sys.stderr = open('/dev/null', 'w')

                # Init Paramiko SSH Connection
                client = paramiko.SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.WarningPolicy())
                client.connect(self._region['ssh']['hostname'], port=self._region['ssh']['port'], username=self._region['ssh']['username'], password=self._region['ssh']['password'], key_filename=self._region['ssh']['key'], timeout=10)
                transport = client.get_transport()
                transport.set_keepalive(30)

                # Show Errors Output Again
                sys.stderr = sys_stderr

                # Paramiko Execute Command
                stdin, stdout, stderr = client.exec_command(command, get_pty=False)
                stdin.close()

                if path:
                    while True:
                        line = stderr.readline()
                        if not line:
                            break
                        with open(path + '.err', 'a') as outfile:
                            outfile.write(line + '\n')

                # Get stdout
                _stdout = stdout.readlines()

                # Return Execution Output
                return _stdout[0].strip() if len(_stdout) > 0 else ''

            except Exception:
                if i == retries - 1:
                    raise

            finally:
                try:
                    client.close()
                except Exception:
                    pass

    def __get(self, remote_path, local_path):
        try:
            # Supress Errors Output
            sys_stderr = sys.stderr
            sys.stderr = open('/dev/null', 'w')

            # Init Paramiko Connection
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(self._region['ssh']['hostname'], port=self._region['ssh']['port'], username=self._region['ssh']['username'], password=self._region['ssh']['password'], key_filename=self._region['ssh']['key'])
            
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
        exception = None
        for _ in range(10):
            try:
                # Init Paramiko Connection
                client = paramiko.SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.WarningPolicy())
                client.connect(self._region['ssh']['hostname'], port=self._region['ssh']['port'], username=self._region['ssh']['username'], password=self._region['ssh']['password'], key_filename=self._region['ssh']['key'], banner_timeout=60)

                # Open sftp connection
                sftp = client.open_sftp()

                # Upload File
                sftp.put(localpath=local_path, remotepath=remote_path, confirm=True)
                break

            except Exception as e:
                exception = e
                time.sleep(2)

            finally:
                try:
                    sftp.close()
                    client.close()
                except Exception:
                    pass
        if exception:
            raise exception
