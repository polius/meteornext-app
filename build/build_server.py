import os
import sys
import shutil
import hashlib
import subprocess
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

if __name__ == '__main__':
    from build_server import build_server
    build_server()

class build_server:
    def __init__(self):
        # Project Base Path
        self._pwd = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/..')

        if len(sys.argv) == 1:
            subprocess.call("python3 build_server.py build_ext meteor", shell=True)
            subprocess.call("python3 build_server.py build_ext server", shell=True)

        elif 'meteor' in sys.argv:
            sys.argv.append("build_ext")
            sys.argv.remove("meteor")
            self.__build_meteor()
        elif 'server' in sys.argv:
            sys.argv.append("build_ext")
            sys.argv.remove("server")
            self.__build_server()

    def __build_meteor(self):
        # Build Meteor Py
        build_path = "{}/meteor".format(self._pwd)
        additional_files = ['query_template.json', 'query_execution.py', 'version.txt']
        additional_binaries = []
        hidden_imports = ['json', 'pymysql','uuid', 'requests', 'imp', 'paramiko', 'boto3', 'socket', 'sshtunnel']
        binary_name = 'meteor'
        binary_path = '{}/server/apps'.format(self._pwd)

        # Generate app version
        version = ''
        files = os.listdir(build_path)
        for f in files:
            if not os.path.isdir("{}/{}".format(build_path, f)) and not f.endswith('.pyc') and not f.startswith('.') and not f.endswith('.gz') and f not in ['version.txt', 'query_execution.py', 'credentials.json']:
                with open("{}/{}".format(build_path, f), 'rb') as file_content:
                    file_hash = hashlib.sha512(file_content.read()).hexdigest()
                    version += file_hash
        with open("{}/version.txt".format(build_path), 'w') as fout:
            fout.write(version)

        # Start Build
        self.__start(build_path, additional_files, additional_binaries, hidden_imports, binary_name, binary_path)

    def __build_server(self):
        # Build Meteor Next Server
        build_path = "{}/server".format(self._pwd)
        additional_files = ['routes/deployments/query_execution.py', 'models/schema.sql', 'apps/meteor.tar.gz']
        hidden_imports = ['json','_cffi_backend','bcrypt','requests','pymysql','uuid','flask','flask_cors','flask_jwt_extended','schedule','boto3','socket','paramiko','sshtunnel']
        additional_binaries = []
        binary_name = 'server'
        binary_path = '{}/dist'.format(self._pwd)
        self.__start(build_path, additional_files, additional_binaries, hidden_imports, binary_name, binary_path)

    ####################
    # INTERNAL METHODS #
    ####################
    def __start(self, build_path, additional_files, additional_binaries, hidden_imports, binary_name, binary_path):
        self.__clean(build_path)
        
        # Clean distpath files
        shutil.rmtree("{}/{}".format(binary_path, binary_name), ignore_errors=True)

        # Copy files to the build dir
        shutil.copytree(build_path, "{}/build".format(build_path))

        # Clean __pycache__ folders in build dir
        for root, dirs, files in os.walk("{}/build".format(build_path)):
            if '__pycache__' in dirs:
                shutil.rmtree("{}/{}".format(root, '__pycache__'), ignore_errors=True)

        # Start building process
        try:
            self.__compile(build_path, binary_name)
            self.__pack(build_path, additional_files, additional_binaries, hidden_imports, binary_name, binary_path)
        finally:
            self.__clean(build_path)

    def __compile(self, build_path, binary_name):
        # Build ext_modules
        ext_modules = []
        for root, dirs, files in os.walk("{}/build".format(build_path)):
            dirs[:] = [d for d in dirs if d not in ['apps']]
            for f in files:
                if f.endswith('.py'):
                    os.rename(os.path.join(root, f), os.path.join(root, f) + 'x')
                    ext_name = os.path.join(root, f)[len(build_path + "/build")+1:-3].replace('/','.')
                    ext_path = '../' + os.path.join(root, f)[len(self._pwd)+1:] + 'x'
                    ext_modules.append(Extension(ext_name, [ext_path]))

        # Start compilation
        setup(
            name=binary_name,
            cmdclass={'build_ext': build_ext},
            ext_modules=cythonize(
                ext_modules,
                build_dir=build_path,
                language_level="3",
                compiler_directives={'always_allow_keywords': True},
                force=True
            )
        )        

    def __pack(self, build_path, additional_files, additional_binaries, hidden_imports, binary_name, binary_path):
        # 4) Get the cythonized directory path
        files = os.listdir("{}/build/build".format(self._pwd))
        for f in files:
            if f.startswith('lib.') and os.path.isdir("{}/{}".format("{}/build".format(self._pwd), f)):
                break
        cythonized = "{}/build/build/{}".format(self._pwd, f)

        # Create apps folder
        if binary_name == 'server':
            os.makedirs("{}/apps".format(cythonized), exist_ok=True)

        # 5) Copy additional files to the cytonized directory path
        for f in additional_files:
            if (os.path.isfile("{}/{}".format(build_path, f))):
                shutil.copyfile("{}/{}".format(build_path, f), "{}/{}".format(cythonized, f))

        # 6) Create 'init.py' to invoke cythonized code
        init_file = "{}/init.py".format(cythonized)
        with open(init_file, 'w') as file_open:
            if binary_name == 'server':
                file_open.write("""# -*- coding: utf-8 -*-
from gunicorn.app.base import Application, Config
import os
import sys
import json
import tarfile
import gunicorn
from gunicorn import glogging
from gunicorn.workers import sync
from app import app

class GUnicornFlaskApplication(Application):
    def __init__(self, app):
        self.usage, self.callable, self.prog, self.app = None, None, None, app

    def run(self, **options):
        self.cfg = Config()
        [self.cfg.set(key, value) for key, value in options.items()]
        return Application.run(self)

    load = lambda self:self.app

if __name__ == "__main__":
    # Extract Meteor
    with tarfile.open("{}/apps/meteor.tar.gz".format(sys._MEIPASS)) as tar:
        tar.extractall(path="{}/apps/meteor/".format(sys._MEIPASS))
    # Init Gunicorn App
    gunicorn_app = GUnicornFlaskApplication(app)
    gunicorn_app.run(worker_class="gunicorn.workers.sync.SyncWorker", bind='unix:server.sock', capture_output=True, errorlog='error.log')""")
            else:
                file_open.write("from {0} import {0}\n{0}()".format(binary_name))

        # 7) Build binaries list
        binaries = []
        for root, dirs, files in os.walk("{}/build".format(self._pwd)):
            for f in files:
                if f.endswith('.so'):
                    binaries.append(f)

        # 8) Build hidden imports
        for root, dirs, files in os.walk("{}/build".format(build_path)):
            for f in files:
                if f.endswith('.pyx'):
                    hidden_imports.append(os.path.join(root, f)[len("{}/build".format(build_path))+1:-4].replace('/','.'))

        # 9) Create "dist" folder
        os.makedirs(binary_path, exist_ok=True)

        # 10) Build pyinstaller command
        command = "cd '{}'; pyinstaller --clean --distpath '{}'".format(cythonized, binary_path)
        for i in hidden_imports:
            command += " --hidden-import={}".format(i)
        for b in binaries:
            command += " -r '{}'".format(b)
        for f in additional_files:
            path = '.' if f.find('/') == -1 else f[:f.rfind('/')]
            command += " --add-data '{}:{}'".format(f, path)
        for b in additional_binaries:
            command += " --add-binary '{}:{}'".format(b[0], b[1])

        if binary_name == 'server':
            command += ' --onefile'
        else:
            command += ' --onedir'
        command += ' "{}/init.py"'.format(cythonized)

        # 11) Pack cythonized project using pyinstaller
        subprocess.call(command, shell=True)

        # 12) Rename pyinstaller file
        os.rename('{}/init'.format(binary_path), '{}/{}'.format(binary_path, binary_name))

        # 13) Compress Meteor
        if binary_name == 'meteor':
            shutil.make_archive('{}/{}'.format(binary_path, binary_name), 'gztar', '{}/{}'.format(binary_path, binary_name))
            shutil.rmtree('{}/{}'.format(binary_path, binary_name), ignore_errors=True)

    def __clean(self, build_path):
        shutil.rmtree("{}/build/build".format(self._pwd), ignore_errors=True)
        shutil.rmtree("{}/dist/logs".format(self._pwd), ignore_errors=True)
        shutil.rmtree("{}/build".format(build_path), ignore_errors=True)
        shutil.rmtree("{}/logs".format(build_path), ignore_errors=True)

        # Delete compiled path
        compile_path = build_path[len(self._pwd)+1:]
        if compile_path.find('/') == -1:
            shutil.rmtree("{}/{}".format(build_path, compile_path), ignore_errors=True)
        else:
            shutil.rmtree("{}/{}".format(build_path, compile_path[:compile_path.find('/')+1]), ignore_errors=True)
