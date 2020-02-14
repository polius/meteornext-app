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
        while option not in ['1','2','3']:
            self.__show_header()
            print("1) Build Docker")
            print("2) Start Docker")
            print("3) Exit")
            option = input("- Select an option: ")

            if option == '1':
                self.build_docker()
            elif option == '2':
                self.start_docker()
            elif option == '3':
                sys.exit()

    def build_docker(self):
        self.__show_header()
        print("|         Build Docker        |")
        print("+=============================+")
        start_time = time.time()
        # Clean Temp Files
        self.clean_docker()
        # Build Server
        self.__build_server()
        # Build Client
        self.__build_client()
        # Build Docker
        subprocess.call("docker pull nginx:latest", shell=True)
        subprocess.call("cd {} ; docker build -t meteornext:latest -f build/docker.dockerfile .".format(self._pwd), shell=True)
        subprocess.call("docker rmi nginx:latest", shell=True)
        subprocess.call("docker save meteornext > {}/dist/meteornext.tar".format(self._pwd), shell=True)
        self.clean_docker()

        print("\n- Build Path: {}/dist/meteornext.tar".format(self._pwd))
        print("- Overall Time: {}".format(time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))))

    def clean_docker(self):
        subprocess.call("rm -rf {}/.cache".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/dist/client.tar.gz".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/dist/server".format(self._pwd), shell=True)
        subprocess.call("docker kill $(docker ps -a -q --filter ancestor=meteornext) >/dev/null 2>&1", shell=True)
        subprocess.call("docker rm $(docker ps -a -q --filter ancestor=meteornext) >/dev/null 2>&1", shell=True)
        subprocess.call("docker rmi meteornext:latest >/dev/null 2>&1", shell=True)

    ####################
    # Internal Methods #
    ####################
    def __build_server(self):
        subprocess.call("rm -rf {}/dist/meteornext.tar".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/dist/server".format(self._pwd), shell=True)
        subprocess.call("docker rmi meteornextbuild:latest >/dev/null 2>&1", shell=True)
        subprocess.call("docker pull amazonlinux:1", shell=True)
        subprocess.call("docker build -t meteornextbuild:latest - < server.dockerfile", shell=True)
        subprocess.call("docker run --rm -it -v {}:/root/ meteornextbuild:latest".format(self._pwd), shell=True)
        subprocess.call("docker rmi meteornextbuild:latest", shell=True)
        subprocess.call("docker rmi amazonlinux:1", shell=True)

    def __build_client(self):
        subprocess.call("rm -rf {}/dist/meteornext.tar".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/dist/client.tar.gz".format(self._pwd), shell=True)
        subprocess.call("cd {}/client ; npm run build".format(self._pwd), shell=True)
        subprocess.call("mv {0}/client/dist {0}/dist/client".format(self._pwd), shell=True)
        subprocess.call("cd {}/dist/ ; tar -czvf client.tar.gz client ; rm -rf client".format(self._pwd), shell=True)

    def __start_docker(self):
        if not os.path.exists("{}/dist/meteornext.tar".format(self._pwd)):
            print("Docker not build. Start building...")
            self.build_docker()

        self.__show_header()
        print("|         Start Docker        |")
        print("+=============================+")
        environment = ''
        option = input("- Assign environment variables? (y/n): ")
        if option == 'y':
            print("+---------+")
            print("| LICENSE |")
            print("+---------+")
            environment += ' -e LIC_EMAIL=' + input("- Email: ")
            environment += ' -e LIC_KEY=' + input("- Key: ")
            print("+---------+")
            print("|   SQL   |")
            print("+---------+")
            environment += ' -e SQL_HOST=' + input("- Hostname: ")
            environment += ' -e SQL_USER=' + input("- Username: ")
            environment += ' -e SQL_PASS=' + input("- Password: ")
            environment += ' -e SQL_PORT=' + input("- Port: ")
            environment += ' -e SQL_DB=' + input("- Database: ")

        print("- Stopping current containers...")
        self.clean_docker()
        print("- Importing image...")
        subprocess.call("docker load -i {}/dist/meteornext.tar".format(self._pwd), shell=True)
        print("- Starting new container...")
        container_id = subprocess.check_output("docker run --name meteornext -itd -p8080:80{} meteornext".format(environment), shell=True)
        print("- Container ID: {}".format(container_id.decode("utf-8")[:12]))

    def __show_header(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("+=============================+")
        print("|         METEOR NEXT         |")
        print("|         - BUILDER -         |")
        print("+=============================+")