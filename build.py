# python3 build.py
import os
import sys
import shutil
import subprocess
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

if __name__ == '__main__':
    from build import build
    build()

class build:
    def __init__(self):
        self._pwd = os.path.dirname(os.path.realpath(__file__))
        
        if len(sys.argv) == 1:
            # subprocess.call("python3 build.py build_ext server", shell=True)
            subprocess.call("python3 build.py build_ext meteor", shell=True)
            # subprocess.call("python3 build.py build_ext client", shell=True)            

        elif 'server' in sys.argv:
            sys.argv.remove("server")
            self.__build_server()
        elif 'meteor' in sys.argv:
            sys.argv.remove("meteor")
            self.__build_meteor()
        elif 'client' in sys.argv:
            subprocess.call("cd client; npm run build", shell=True)

    def __build_server(self):
        # Build Meteor Next Server
        build_path = "{}/server".format(self._pwd)
        additional_files = ['credentials.json']
        hidden_imports = ['json','_cffi_backend','bcrypt','pymysql','uuid','flask','flask_cors','flask_jwt_extended','schedule','boto3']
        binary_name = 'server'
        self.__start(build_path, additional_files, hidden_imports, binary_name)

    def __build_meteor(self):
        # Build Meteor Py
        build_path = "{}/apps/Meteor/app".format(self._pwd)
        additional_files = ['query_template.json']
        hidden_imports = ['json', 'pymysql','uuid', 'requests', 'imp', 'paramiko', 'boto3']
        binary_name = 'meteor'
        self.__start(build_path, additional_files, hidden_imports, binary_name)

    ####################
    # INTERNAL METHODS #
    ####################
    def __start(self, build_path, additional_files, hidden_imports, binary_name):
        self.__clean(build_path)
        shutil.copytree(build_path, "{}/build".format(build_path))

        for root, dirs, files in os.walk("{}/build".format(build_path)):
            if '__pycache__' in dirs:
                shutil.rmtree("{}/{}".format(root, '__pycache__'), ignore_errors=True)

        # Start building process
        try:
            self.__compile(build_path, binary_name)
            self.__pack(build_path, additional_files, hidden_imports, binary_name)
        finally:
            self.__clean(build_path)

    def __compile(self, build_path, binary_name):
        # Build ext_modules
        ext_modules = []
        for root, dirs, files in os.walk("{}/build".format(build_path)):
            for f in files:
                if f.endswith('.py'):
                    os.rename(os.path.join(root, f), os.path.join(root, f) + 'x')
                    ext_name = os.path.join(root, f)[len(build_path + "/build")+1:-3].replace('/','.')
                    ext_path = os.path.join(root, f)[len(self._pwd)+1:] + 'x'
                    ext_modules.append(Extension(ext_name, [ext_path]))

        # Start compilation
        setup(
            name=binary_name,
            cmdclass={'build_ext': build_ext},
            ext_modules=cythonize(
                ext_modules,
                build_dir=build_path,
                language_level="3",
                compiler_directives={'always_allow_keywords': True}
            )
        )

    def __pack(self, build_path, additional_files, hidden_imports, binary_name):
        # 4) Get the cythonized directory path
        files = os.listdir("{}/build".format(self._pwd))
        for f in files:
            if f.startswith('lib.') and os.path.isdir("{}/{}".format("{}/build".format(self._pwd), f)):
                break
        cythonized = "{}/build/{}".format(self._pwd, f)

        # 5) Copy additional files to the cytonized directory path
        for f in additional_files:
            if (os.path.isfile("{}/{}".format(build_path, f))):
                shutil.copyfile("{}/{}".format(build_path, f), "{}/{}".format(cythonized, f))

        # 6) Create 'init.py' to invoke cythonized code
        init_file = "{}/init.py".format(cythonized)
        with open(init_file, 'w') as file_open:
            if binary_name == 'server':
                file_open.write("from app import app")
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

        # 9) Create dist folder
        if not os.path.isdir('{}/dist'.format(self._pwd)):
            os.mkdir('{}/dist'.format(self._pwd))

        # 10) Build pyinstaller command
        command = "cd '{}'; pyinstaller --distpath '{}/dist'".format(cythonized, self._pwd)
        for i in hidden_imports:
            command += " --hidden-import={}".format(i)
        for b in binaries:
            command += " -r '{}'".format(b)
        for f in additional_files:
            command += " --add-data '{}:.'".format(f)
        command += ' --onefile "{}/init.py"'.format(cythonized)

        # 11) Pack cythonized project using pyinstaller
        subprocess.call(command, shell=True)

        # 12) Rename pyinstaller file
        os.rename('{}/dist/init'.format(self._pwd), '{}/dist/{}'.format(self._pwd, binary_name))

    def __clean(self, build_path):
        shutil.rmtree("{}/build".format(build_path), ignore_errors=True)
        shutil.rmtree("{}/build".format(self._pwd), ignore_errors=True)
        shutil.rmtree("{}/logs".format(build_path), ignore_errors=True)

        # Delete compiled path
        compile_path = build_path[len(self._pwd)+1:]
        if compile_path.find('/') == -1:
            shutil.rmtree("{}/{}".format(build_path, compile_path), ignore_errors=True)
        else:
            shutil.rmtree("{}/{}".format(build_path, compile_path[:compile_path.find('/')+1]), ignore_errors=True)