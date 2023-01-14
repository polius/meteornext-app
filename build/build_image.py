import os
import sys
import shutil
import hashlib
import subprocess
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize
# from PyInstaller.utils.hooks import collect_submodules

if __name__ == '__main__':
    from build_image import build_image
    build_image()

class build_image:
    def __init__(self):
        # Project Base Path
        self._pwd = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/..')

        if len(sys.argv) == 1:
            if os.environ['TARGET'] == 'meteor':
                pass
            elif os.environ['TARGET'] == 'image':
                # Build meteor
                subprocess.call("python3 build_image.py build_ext meteor", shell=True)
                # Build backend
                subprocess.call("python3 build_image.py build_ext server", shell=True)
                # Build frontend
                subprocess.call("rm -rf /root/dist/client.tar.gz", shell=True)
                subprocess.call("cd /root/client ; npm run build", shell=True)
                subprocess.call("mv /root/client/dist /root/dist/client", shell=True)
                subprocess.call("cd /root/dist/ ; tar -czvf client.tar.gz client ; rm -rf client", shell=True)
                subprocess.call("rm -rf /root/.config", shell=True)

        elif 'meteor' in sys.argv:
            sys.argv.append("build_ext")
            sys.argv.remove("meteor")
            self.__build_meteor()
        elif 'server' in sys.argv:
            sys.argv.append("build_ext")
            sys.argv.remove("server")
            self.__build_server()

    def __build_meteor(self):
        # Generate App Version
        version = ''
        files = os.listdir(f"{self._pwd}/meteor")
        for f in files:
            if not os.path.isdir(f"{self._pwd}/meteor/{f}") and not f.endswith('.pyc') and not f.startswith('.') and not f.endswith('.gz') and f not in ['version.txt', 'blueprint.py', 'config.json']:
                with open(f"{self._pwd}/meteor/{f}", 'rb') as file_content:
                    file_hash = hashlib.sha512(file_content.read()).hexdigest()
                    version += file_hash
        with open(f'{self._pwd}/meteor/version.txt', 'w') as file_content:
            file_content.write(version)

        # Build Meteor Py
        build_path = f"{self._pwd}/meteor"
        additional_files = ['version.txt']
        additional_binaries = []
        hidden_imports = ['pymysql','requests','paramiko','boto3','sshtunnel','sentry_sdk','sqlparse','urllib3','charset_normalizer.md__mypyc']
        binary_name = 'meteor'
        binary_path = f'{self._pwd}/server/apps'

        # Start Build
        self.__start(build_path, additional_files, additional_binaries, hidden_imports, binary_name, binary_path)

    def __build_server(self):
        # Build Meteor Next Server
        build_path = f"{self._pwd}/server"
        additional_files = ['routes/deployments/blueprint.py', 'models/schema.sql', 'apps/meteor.tar.gz']
        hidden_imports = ['_cffi_backend','bcrypt','requests','pymysql','flask','flask_cors','flask_jwt_extended','schedule','boto3','paramiko','sshtunnel','pyotp','flask_compress','dbutils.pooled_db','statistics','re','webauthn','sentry_sdk','sqlparse','gunicorn.app.base','gunicorn.glogging','gunicorn.workers.gthread','charset_normalizer.md__mypyc']
        additional_binaries = []
        binary_name = 'server'
        binary_path = f'{self._pwd}/dist'
        self.__start(build_path, additional_files, additional_binaries, hidden_imports, binary_name, binary_path)

    ####################
    # INTERNAL METHODS #
    ####################
    def __start(self, build_path, additional_files, additional_binaries, hidden_imports, binary_name, binary_path):
        self.__clean(build_path)
        
        # Clean distpath files
        shutil.rmtree(f"{binary_path}/{binary_name}", ignore_errors=True)

        # Copy files to the build dir
        shutil.copytree(build_path, f"{build_path}/build")

        # Clean __pycache__ folders in build dir
        for root, dirs, files in os.walk(f"{build_path}/build"):
            if '__pycache__' in dirs:
                shutil.rmtree(f"{root}/__pycache__", ignore_errors=True)

        # Clean files folder
        if binary_name == 'server':
            shutil.rmtree(f"{build_path}/build/files", ignore_errors=True)

        # Start building process
        try:
            self.__compile(build_path, binary_name)
            self.__pack(build_path, additional_files, additional_binaries, hidden_imports, binary_name, binary_path)
        finally:
            self.__clean(build_path)

    def __compile(self, build_path, binary_name):
        # Build ext_modules
        ext_modules = []
        for root, dirs, files in os.walk(f"{build_path}/build"):
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
        files = os.listdir(f"{self._pwd}/build/build")
        for f in files:
            if f.startswith('lib.') and os.path.isdir(f"{self._pwd}/build/{f}"):
                break
        cythonized = f"{self._pwd}/build/build/{f}"

        # Create apps folder
        if binary_name == 'server':
            os.makedirs(f"{cythonized}/apps", exist_ok=True)

        # 5) Copy additional files to the cytonized directory path
        for f in additional_files:
            if (os.path.isfile(f"{build_path}/{f}")):
                shutil.copyfile(f"{build_path}/{f}", f"{cythonized}/{f}")

        # 6) Create 'init.py' to invoke cythonized code
        init_file = f"{cythonized}/init.py"
        with open(init_file, 'w') as file_open:
            file_open.write(f"from {binary_name} import {binary_name}\n{binary_name}()")

        # 7) Build binaries list
        binaries = []
        for root, dirs, files in os.walk(f"{self._pwd}/build"):
            for f in files:
                if f.endswith('.so'):
                    binaries.append(f)

        # 8) Build hidden imports
        for root, dirs, files in os.walk(f"{build_path}/build"):
            for f in files:
                if f.endswith('.pyx'):
                    hidden_imports.append(os.path.join(root, f)[len(f"{build_path}/build")+1:-4].replace('/','.'))

        # 9) Create "dist" folder
        os.makedirs(binary_path, exist_ok=True)

        # 10) Setup UPX
        subprocess.call("curl -L https://github.com/upx/upx/releases/download/v3.96/upx-3.96-amd64_linux.tar.xz --output /tmp/upx-3.96-amd64_linux.tar.xz", shell=True)
        subprocess.call("tar xvfJ /tmp/upx-3.96-amd64_linux.tar.xz -C /tmp", shell=True)

        # 11) Build pyinstaller command
        command = f"cd '{cythonized}'; python3 -m PyInstaller --clean --distpath '{binary_path}'"
        for i in hidden_imports:
            command += f" --hidden-import={i}"
            # for m in collect_submodules(i):
            #     command += f" --hidden-import={m}"
        for b in binaries:
            command += f" -r '{b}'"
        for f in additional_files:
            path = '.' if f.find('/') == -1 else f[:f.rfind('/')]
            command += f" --add-data '{f}:{path}'"
        for b in additional_binaries:
            command += f" --add-binary '{b[0]}:{b[1]}'"

        command += ' --upx-dir /tmp/upx-3.96-amd64_linux'
        command += f'--onedir "{cythonized}/init.py"'

        # 12) Pack cythonized project using pyinstaller
        subprocess.call(command, shell=True)

        # 13) Rename pyinstaller file
        os.rename(f'{binary_path}/init', f'{binary_path}/{binary_name}')

        # 14) Compress Meteor
        if binary_name == 'meteor':
            shutil.make_archive(f'{binary_path}/{binary_name}', 'gztar', f'{binary_path}/{binary_name}')
            shutil.rmtree(f'{binary_path}/{binary_name}', ignore_errors=True)

    def __clean(self, build_path):
        shutil.rmtree(f"{self._pwd}/build/build", ignore_errors=True)
        shutil.rmtree(f"{self._pwd}/dist/logs", ignore_errors=True)
        shutil.rmtree(f"{build_path}/build", ignore_errors=True)
        shutil.rmtree(f"{build_path}/logs", ignore_errors=True)

        # Delete compiled path
        compile_path = build_path[len(self._pwd)+1:]
        if compile_path.find('/') == -1:
            shutil.rmtree(f"{build_path}/{compile_path}", ignore_errors=True)
        else:
            shutil.rmtree(f"{build_path}/{compile_path[:compile_path.find('/')+1]}", ignore_errors=True)
