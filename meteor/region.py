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
        self._remote_path = "$HOME/.meteor" if region['ssh']['enabled'] else None
        # Get UUID from path
        self._uuid = self._args.path[self._args.path.rfind('/')+1:]

    def check_version(self):
        # Get SSH Version
        ssh_version = self.__ssh("cat {}/bin/version.txt".format(self._remote_path), None)
        if len(ssh_version) == 0:
            return False

        # Get Local Version
        with open("{}/version.txt".format(self._local_path)) as file_content:
            local_version = file_content.read()

        # Compare Local & SSH Version
        return local_version == ssh_version

    def upload_binary(self):
        # Get Remote Home Path
        home = self.__ssh("echo $HOME", None)

        # Upload Binary
        if self._bin:
            self.__ssh("rm -rf {0}/bin && mkdir -p {0}/bin".format(self._remote_path), None)
            self.__put("{}.tar.gz".format(self._local_path), "{}/.meteor/bin/meteor.tar.gz".format(home))
            self.__ssh("tar -xvzf {0}/bin/meteor.tar.gz -C {0}/bin && rm -rf {0}/bin/meteor.tar.gz".format(self._remote_path), None)
        else:
            # Compress Meteor files
            shutil.make_archive(self._local_path, 'gztar', self._local_path)
            shutil.move("{}.tar.gz".format(self._local_path), "{}/../server/apps/meteor.tar.gz".format(self._local_path))
            # Upload Meteor
            self.__ssh("rm -rf {0}/bin && mkdir -p {0}/bin".format(self._remote_path), None)
            self.__put("{}/../server/apps/meteor.tar.gz".format(self._local_path), "{}/.meteor/bin/meteor.tar.gz".format(home))
            self.__ssh("tar -xvzf {0}/bin/meteor.tar.gz -C {0}/bin && rm -rf {0}/bin/meteor.tar.gz".format(self._remote_path), None)

    def get_logs(self):
        # Get Remote Home Path
        home = self.__ssh("echo $HOME", None)

        # 1. Compress Logs
        binary_path = "{}/bin/init".format(self._remote_path) if self._bin else "python3 {}/bin/meteor.py".format(self._remote_path)
        self.__ssh('{} --path "{}/logs/{}" --region "{}" --compress'.format(binary_path, self._remote_path, self._uuid, self._region['name']), None)
        # 2. Download Compressed Logs
        remote_path = "{}/.meteor/logs/{}/execution/{}.tar.gz".format(home, self._uuid, self._region['name'])
        local_path = "{}/execution/{}.tar.gz".format(self._args.path, self._region['name'])
        status = self.__get(remote_path, local_path)

        if status:
            # 3. Uncompress Downloaded Logs
            with tarfile.open(local_path) as tar:
                tar.extractall(path="{}/execution".format(self._args.path))

            # 4. Delete Downloaded Compressed Logs
            os.remove(local_path)

    def get_progress(self):
        current_thread = threading.current_thread()

        if self._region['ssh']['enabled']:
            progress = self.__ssh("cat {}/logs/{}/execution/{}/progress.json 2>/dev/null".format(self._remote_path, self._uuid, self._region['name']), None)
        else:
            progress = self.__local("cat {}/execution/{}/progress.json 2>/dev/null".format(self._args.path, self._region['name']), None)
        current_thread.progress = json.loads(progress) if len(progress) > 0 else {}

    def clean(self):
        self.__ssh("rm -rf {}/logs/{}".format(self._remote_path, self._uuid), None)

    def check_processes(self):
        # Check Processes Currently Executing
        command = "ps -U $USER -u $USER u | grep '{}' | grep '\-\-region' | grep -v grep | awk '{{print $2}}' | wc -l".format(self._uuid)
        count = self.__ssh(command, None) if self._region['ssh']['enabled'] else self.__local(command, None)
        return int(count)

    def sigint(self):
        command = "ps -U $USER -u $USER u | grep '{}' | grep -v grep | awk '{{print $2}}' | xargs kill -2 2> /dev/null".format(self._uuid)
        if self._region['ssh']['enabled']:
            self.__ssh(command, self._args.path + '/logs/' + self._region['name'])
        else:
            self.__local(command, self._args.path + '/logs/' + self._region['name'])

    def sigkill(self):
        command = "ps -U $USER -u $USER u | grep '{}' | grep -v grep | awk '{{print $2}}' | xargs kill -9 2> /dev/null".format(self._uuid)
        if self._region['ssh']['enabled']:
            self.__ssh(command, None)
        else:
            self.__local(command, None)

    ##########
    # REMOTE #
    ##########
    def deploy(self):
        # Deploy new execution
        mode = 'validate' if self._args.validate else 'test' if self._args.test else 'deploy'
        
        if self._region['ssh']['enabled']:
            home = self.__ssh("echo $HOME", None)
            binary_path = "{}/bin/init".format(self._remote_path) if self._bin else "python3 {}/bin/meteor.py".format(self._remote_path)

            # Upload execution
            self.__ssh('mkdir -p {}/logs/{}'.format(self._remote_path, self._uuid), None)
            self.__put("{}/config.json".format(self._args.path), "{}/.meteor/logs/{}/config.json".format(home, self._uuid))
            self.__put("{}/blueprint.py".format(self._args.path), "{}/.meteor/logs/{}/blueprint.py".format(home, self._uuid))

            # Start execution
            # self.__ssh('nohup {} --path "{}/logs/{}" --{} --region "{}" </dev/null >/dev/null 2>&1 &'.format(binary_path, self._remote_path, self._uuid, mode, self._region['name']))
            self.__ssh('{} --path "{}/logs/{}" --{} --region "{}"'.format(binary_path, self._remote_path, self._uuid, mode, self._region['name']), self._args.path + '/logs/' + self._region['name'])
        else:
            binary_path = "{}/init".format(self._local_path) if self._bin else "python3 {}/meteor.py".format(self._local_path)
            # Start execution
            # self.__local('nohup {} --path "{}" --{} --region "{}" </dev/null >/dev/null 2>&1 &'.format(binary_path, self._args.path, mode, self._region['name']))
            self.__local('{} --path "{}" --{} --region "{}"'.format(binary_path, self._args.path, mode, self._region['name']), self._args.path + '/logs/' + self._region['name'])

        # Wait deploy to finish
        while self.check_processes() > 0:
            time.sleep(1)

    def compress_logs(self):
        compressed_dir = "{}/execution/{}".format(self._args.path, self._region['name'])
        compressed_path = "{}/execution".format(self._args.path)
        shutil.make_archive(compressed_dir, 'gztar', compressed_path)

    ################
    # Core Methods #
    ################
    def __local(self, command, path):
        # Paramiko Execute Local Command
        client = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # for line in client.stderr:
        #     print(line.rstrip())

        # Get stdout & stderr
        stdout = client.stdout.readlines()
        stderr = client.stderr.readlines()

        # Log response
        if path:
            with open(path + '.txt', "a") as myfile:
                myfile.write(command)
                myfile.write("\nstdout: " + str(stdout))
                myfile.write("\nstderr: " + str(stderr))

        # Return Execution Output
        return stdout[0] if len(stdout) > 0 else ''

    def __ssh(self, command, path):
        try:
            # Supress Errors Output
            sys_stderr = sys.stderr
            sys.stderr = open('/dev/null', 'w')

            # Init Paramiko SSH Connection
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(self._region['ssh']['hostname'], port=self._region['ssh']['port'], username=self._region['ssh']['username'], password=self._region['ssh']['password'], key_filename=self._region['ssh']['key'])
            transport = client.get_transport()
            transport.set_keepalive(30)

            # Show Errors Output Again
            sys.stderr = sys_stderr

            # Paramiko Execute Command
            stdin, stdout, stderr = client.exec_command(command, get_pty=False)
            stdin.close()

            # for line in stderr:
            #     print(line.rstrip())

            # Get stdout & stderr
            _stdout = stdout.readlines()
            _stderr = stderr.readlines()

            # Log response
            if path:
                with open(path + '.txt', "a") as myfile:
                    myfile.write(command)
                    myfile.write("\nstdout: " + str(_stdout))
                    myfile.write("\nstderr: " + str(_stderr))

            # Return Execution Output
            return _stdout[0].strip() if len(_stdout) > 0 else ''

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
        try:
            # Init Paramiko Connection
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
            client.connect(self._region['ssh']['hostname'], port=self._region['ssh']['port'], username=self._region['ssh']['username'], password=self._region['ssh']['password'], key_filename=self._region['ssh']['key'])

            # Open sftp connection
            sftp = client.open_sftp()

            # Upload File
            sftp.put(local_path, remote_path)

        finally:
            if 'sftp' in locals():
                sftp.close()
