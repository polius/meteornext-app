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
            print("1) Build Local")
            print("2) Build Docker")
            print("3) Exit")
            option = input("- Select an option: ")

            if option == '1':
                self.build_binaries()
            elif option == '2':
                self.build_docker()
            elif option == '3':
                sys.exit()

    def build_binaries(self):
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

    def build_docker(self):
        pass

    ####################
    # Internal Methods #
    ####################
    def __build_server(self):
        subprocess.call("docker image rm meteornextbuild:latest", shell=True)
        subprocess.call("docker build -t meteornextbuild:latest - < server.dockerfile", shell=True)
        subprocess.call("docker run --rm -it -v {}:/root/ meteornextbuild:latest".format(self._pwd), shell=True)
        subprocess.call("docker image rm meteornextbuild:latest", shell=True)

    def __build_client(self):
        subprocess.call("cd {}/client ; npm run build".format(self._pwd), shell=True)
        subprocess.call("mv {0}/client/dist {0}/dist/client".format(self._pwd), shell=True)

    def __show_header(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("+=============================+")
        print("|         METEOR NEXT         |")
        print("|         - BUILDER -         |")
        print("+=============================+")