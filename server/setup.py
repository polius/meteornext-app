# python3 setup.py build_ext
# pyinstaller --add-data 'credentials.json:.' --hidden-import=_cffi_backend --hidden-import=pymysql --onefile app.py
import os
import shutil
import subprocess
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

pwd = os.path.dirname(os.path.realpath(__file__))
build = "{}/build".format(pwd)

# 1) Recreate 'build' folder with a copy of all backend files
shutil.rmtree(build, ignore_errors=True)
shutil.copytree(pwd, build)
shutil.rmtree("{}/logs".format(build), ignore_errors=True)
os.remove("{}/setup.py".format(build))

# 1.2) Remove __pycache__ folder from all project
for root, dirs, files in os.walk(build):
    if '__pycache__' in dirs:
        shutil.rmtree("{}/{}".format(root, '__pycache__'), ignore_errors=True)

# 2) Build ext_modules
ext_modules = []
for root, dirs, files in os.walk(build):
    for f in files:
        if f.endswith('.py'):
            os.rename(os.path.join(root, f), os.path.join(root, f) + 'x')
            ext_name = 'build.' + os.path.join(root, f)[len(build)+1:-3].replace('/','.')
            ext_path = 'build/' + os.path.join(root, f)[len(build)+1:] + 'x'
            ext_modules.append(Extension(ext_name, [ext_path]))

# 3) Start compilation
setup(
    name='Meteor Next',
    cmdclass={'build_ext': build_ext},
    ext_modules=cythonize(
        ext_modules,
        language_level="3",
        compiler_directives={'always_allow_keywords': True}
    )
)

# 4) Get the cythonized directory path
files = os.listdir(build)
for f in files:
    if f.startswith('lib.') and os.path.isdir("{}/{}".format(build, f)):
        break
cythonized = "{}/{}/build".format(build, f)

# 5) Move 'credentials.json' to the cytonized directory path
shutil.move("{}/credentials.json".format(build), "{}/credentials.json".format(cythonized))

# 6) Create 'meteor.py' to invoke cythonized code
init_file = "{}/meteor.py".format(cythonized)
with open(init_file, 'w') as file_open:
    file_open.write("from app import app")

# 7) Build binaries list
binaries = []
for root, dirs, files in os.walk(build):
    for f in files:
        if f.endswith('.so'):
            binaries.append(f)

# 8) Build hidden imports
hidden_imports = ['json','_cffi_backend','pymysql','uuid']

# 8) Build pyinstaller command
command = "cd '{}'; pyinstaller --distpath '{}' --add-data 'credentials.json:.'".format(cythonized, pwd)
for i in hidden_imports:
    command += " --hidden-import={}".format(i)
for b in binaries:
    command += " -r '{}'".format(b)
command += ' --onefile meteor.py'

# 9) Pack cythonized project using pyinstaller
p = subprocess.call(command, stdout=open('/dev/null', 'w'), shell=True)

# 11) Clean build data
shutil.rmtree(build)