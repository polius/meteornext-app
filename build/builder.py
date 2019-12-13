import os
import sys
import time
import subprocess

if __name__ == '__main__':
    from builder import builder
    builder()

class builder:
    def __init__(self):
        self._pwd = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/..')
        self.menu()

    def menu(self):
        option = ''
        while option not in ['1','2','3','4']:
            self.__show_header()
            print("1) Build Project")
            print("2) Build Docker")
            print("3) Start Docker")
            print("4) Exit")
            option = input("- Select an option: ")

            if option == '1':
                self.build_project()
            elif option == '2':
                self.build_docker()
            elif option == '3':
                self.start_docker()
            elif option == '4':
                sys.exit()

    def build_project(self):
        self.__show_header()
        option = ''
        while option not in ['1','2','3','4']:
            print("|         Build Local         |")
            print("+=============================+")
            print("1) Build Server & Client")
            print("2) Build Server")
            print("3) Build Client")
            print("4) Go to menu")
            option = input("- Select an option: ")
            start_time = time.time()

            if option == '1':
                self.__build_server()
                self.__build_client()
            elif option == '2':
                self.__build_server()                
            elif option == '3':
                self.__build_client()
            elif option == '4':
                self.menu()

            if option in ['1','2','3']:
                self.__show_header()
                print("- Distribution Path: '{}/dist/'".format(self._pwd))
                print("- Overall Time: {}".format(time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))))
                option2 = input("- Build Docker? (y/n): ")
                if option2 == 'y':
                    self.build_docker()

    def build_docker(self):
        self.__show_header()
        print("|         Build Docker        |")
        print("+=============================+")
        start_time = time.time()
        subprocess.call("docker rmi meteornext:latest >/dev/null 2>&1", shell=True)
        subprocess.call("docker pull nginx:latest", shell=True)
        subprocess.call("cd {} ; docker build -t meteornext:latest -f build/docker.dockerfile .".format(self._pwd), shell=True)
        subprocess.call("docker rmi nginx:latest", shell=True)

        self.__show_header()
        print("- Overall Time: {}".format(time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))))
        option = input("- Start container? (y/n): ")
        if option == 'y':
            self.start_docker()

    def start_docker(self):
        self.__show_header()
        print("|         Start Docker        |")
        print("+=============================+")
        environment = ''
        option = input("- Assign environment variables? (y/n): ")
        if option == 'y':
            environment += ' -e HOST=' + input("- HOST: ")
            environment += ' -e USER=' + input("- USER: ")
            environment += ' -e PASS=' + input("- PASS: ")
            environment += ' -e PORT=' + input("- PORT: ")
            environment += ' -e DB=' + input("- DB: ")

        print("- Starting new container...")
        subprocess.call("docker kill $(docker ps -a -q --filter ancestor=meteornext) >/dev/null 2>&1", shell=True)
        container_id = subprocess.check_output("docker run --name meteornext -itd -p8080:80{} meteornext".format(environment), shell=True)
        print("- Container ID: {}".format(container_id.decode("utf-8")[:12]))

    ####################
    # Internal Methods #
    ####################
    def __build_server(self):
        subprocess.call("docker rmi meteornextbuild:latest >/dev/null 2>&1", shell=True)
        subprocess.call("docker pull amazonlinux:1", shell=True)
        subprocess.call("docker build -t meteornextbuild:latest - < server.dockerfile", shell=True)
        subprocess.call("docker run --rm -it -v {}:/root/ meteornextbuild:latest".format(self._pwd), shell=True)
        subprocess.call("docker rmi meteornextbuild:latest", shell=True)
        subprocess.call("docker rmi amazonlinux:1", shell=True)

    def __build_client(self):
        subprocess.call("cd {}/client ; npm run build".format(self._pwd), shell=True)
        subprocess.call("mv {0}/client/dist {0}/dist/client".format(self._pwd), shell=True)
        subprocess.call("cd {}/dist/ ; tar -czvf client.tar.gz client ; rm -rf client".format(self._pwd), shell=True)

    def __show_header(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("+=============================+")
        print("|         METEOR NEXT         |")
        print("|         - BUILDER -         |")
        print("+=============================+")