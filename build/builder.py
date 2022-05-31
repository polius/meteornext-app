import os
import time
import subprocess

if __name__ == '__main__':
    from builder import builder
    builder()

class builder:
    def __init__(self):
        self._pwd = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/..')
        self.build_docker()

    def build_docker(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("+=============================+")
        print("|         METEOR NEXT         |")
        print("|         - BUILDER -         |")
        print("+=============================+")
        start_time = time.time()
        # Clean Temp Files
        self.__clean_docker()
        # Build Server
        self.__build_server()
        # Build Client
        self.__build_client()
        # Build Docker
        subprocess.call("docker pull nginx:latest", shell=True)
        subprocess.call("cd {} ; docker buildx build -t meteornext:latest -f build/docker.dockerfile --no-cache --platform linux/amd64 --load .".format(self._pwd), shell=True)
        subprocess.call("docker save meteornext | gzip -9 > {}/dist/meteornext.tar.gz".format(self._pwd), shell=True)
        self.__clean_docker()
        print("\n- Build Path: {}/dist/meteornext.tar.gz".format(self._pwd))
        print("- Overall Time: {}".format(time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))))

    ####################
    # Internal Methods #
    ####################
    def __build_server(self):
        subprocess.call("rm -rf {}/dist/meteornext.tar.gz".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/dist/server".format(self._pwd), shell=True)
        subprocess.call("docker rmi meteornextbuild:latest >/dev/null 2>&1", shell=True)
        subprocess.call("docker pull amazonlinux:1", shell=True)
        # One Time: create a new builder instance to be able to build for multiplatform
        # docker buildx create --use
        subprocess.call("docker buildx build -t meteornextbuild:latest --no-cache --platform linux/amd64 --load - < server.dockerfile", shell=True)
        subprocess.call("docker run --rm -it -v {}:/root/ meteornextbuild:latest".format(self._pwd), shell=True)
        subprocess.call("docker rmi meteornextbuild:latest", shell=True)
        subprocess.call("docker buildx prune --force >/dev/null 2>&1", shell=True)

    def __build_client(self):
        subprocess.call("rm -rf {}/dist/meteornext.tar.gz".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/dist/client.tar.gz".format(self._pwd), shell=True)
        subprocess.call("cd {}/client ; npm run build".format(self._pwd), shell=True)
        subprocess.call("mv {0}/client/dist {0}/dist/client".format(self._pwd), shell=True)
        subprocess.call("cd {}/dist/ ; tar -czvf client.tar.gz client ; rm -rf client".format(self._pwd), shell=True)

    def __clean_docker(self):
        subprocess.call("sudo rm -rf {}/.cache".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/dist/client.tar.gz".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/dist/server".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/server/apps/meteor.tar.gz".format(self._pwd), shell=True)
        subprocess.call("rm -rf {}/server/apps/monitor.tar.gz".format(self._pwd), shell=True)
        subprocess.call("docker kill $(docker ps -a -q --filter ancestor=meteornext) >/dev/null 2>&1", shell=True)
        subprocess.call("docker rm $(docker ps -a -q --filter ancestor=meteornext) >/dev/null 2>&1", shell=True)
        subprocess.call("docker rmi meteornext:latest >/dev/null 2>&1", shell=True)
        subprocess.call("docker buildx prune --force >/dev/null 2>&1", shell=True)
