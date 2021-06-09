import os
import sys
import time
import subprocess

if __name__ == '__main__':
    from build import build
    build()

class build:
    def __init__(self):
        self._pwd = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/..')
        self.menu()

    def menu(self):
        option = ''
        while option not in ['1','2','3','4']:
            self.__show_header()
            print("1) Build Docker")
            print("2) Start Container")
            print("3) Clean Container")
            print("4) Exit")
            option = input("- Select an option: ")

            if option == '1':
                self.build()
            elif option == '2':
                self.start()
            elif option == '3':
                self.clean()
            elif option == '4':
                sys.exit()

    def build(self):
        self.__show_header()
        print("|           Build            |")
        print("+============================+")
        start_time = time.time()
        self.clean()
        os.makedirs('{}/dist'.format(self._pwd), exist_ok=True)
        subprocess.call("docker pull nginx:alpine", shell=True)
        subprocess.call("cd {} ; docker build -t licenser:latest -f build/Dockerfile .".format(self._pwd), shell=True)
        subprocess.call("docker rmi nginx:alpine", shell=True)
        subprocess.call("docker save licenser > {}/dist/licenser.tar".format(self._pwd), shell=True)
        self.clean()

        print("\n- Build Path: {}/dist/licenser.tar".format(self._pwd))
        print("- Overall Time: {}".format(time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))))

        option = input("- Start container? (y/n): ")
        if option == 'y':
            self.start()

    def start(self):
        if not os.path.exists("{}/dist/licenser.tar".format(self._pwd)):
            print("Docker not build. Start building...")
            self.build()

        self.__show_header()
        print("|           Start            |")
        print("+============================+")
        environment = ''
        option = input("- Assign environment variables? (y/n): ")
        if option == 'y':
            environment = ''
            environment += ' -e HOST=' + input("- HOST: ")
            environment += ' -e USER=' + input("- USER: ")
            environment += ' -e PASS=' + input("- PASS: ")
            environment += ' -e PORT=' + input("- PORT: ")
            environment += ' -e DB=' + input("- DB: ")

        print("- Stopping current containers...")
        self.clean()
        print("- Importing image...")
        subprocess.call("docker load -i {}/dist/licenser.tar".format(self._pwd), shell=True)
        print("- Starting new container...")
        container_id = subprocess.check_output("docker run --name licenser -itd -p12350:80{} licenser".format(environment), shell=True)
        print("- Container ID: {}".format(container_id.decode("utf-8")[:12]))

    def clean(self):
        subprocess.call("docker kill $(docker ps -a -q --filter ancestor=licenser) >/dev/null 2>&1", shell=True)
        subprocess.call("docker rm $(docker ps -a -q --filter ancestor=licenser) >/dev/null 2>&1", shell=True)
        subprocess.call("docker rmi licenser:latest >/dev/null 2>&1", shell=True)

    ####################
    # Internal Methods #
    ####################
    def __show_header(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("+============================+")
        print("|          LICENSER          |")
        print("+============================+")