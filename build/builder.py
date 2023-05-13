import os
import time
import subprocess

if __name__ == '__main__':
    from builder import builder
    builder()

class builder:
    def __init__(self):
        self._version = '1.0.5'
        self._pwd = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/..')
        self.build_docker()

    def build_docker(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("+=============================+")
        print("|         METEOR NEXT         |")
        print("|         - BUILDER -         |")
        print("+=============================+")
        start_time = time.time()
        # Clean old dist
        subprocess.call(f"sudo rm -rf {self._pwd}/dist/meteornext.tar.gz", shell=True)
        # Clean Temp Files
        self.__clean()
        # Build Base Image
        # self.__build_base()
        # Build Image
        self.__build_image()
        # Upload Image
        self.__upload_image()
        # Clean
        self.__clean()
        print(f"\n- Build Path: {self._pwd}/dist/meteornext.tar.gz")
        print(f"- Overall Time: {time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))}")

    ####################
    # Internal Methods #
    ####################
    def __build_base(self):
        arch = 'amd64'
        docker_from = 'amazonlinux:1' if arch == 'amd64' else 'amazonlinux:2'
        subprocess.call(f"docker rmi meteornextbase >/dev/null 2>&1", shell=True)
        subprocess.call(f"docker buildx build -t meteornextbase --build-arg FROM='{docker_from}' --no-cache --platform linux/{arch} --load - < base.dockerfile", shell=True)

    def __build_image(self):
        # Clean previous builds
        subprocess.call(f"sudo rm -rf {self._pwd}/dist/client.tar.gz", shell=True)
        subprocess.call(f"sudo rm -rf {self._pwd}/dist/server", shell=True)
        # Build backend & frontend
        subprocess.call(f"docker buildx build -t meteornextbuild:latest --build-arg FROM='meteornextbase' --no-cache --platform linux/amd64 --load - < build.dockerfile", shell=True)
        subprocess.call(f"docker run --rm -it -v {self._pwd}:/root/ -e TARGET=image meteornextbuild:latest", shell=True)
        subprocess.call("docker rmi meteornextbuild:latest", shell=True)
        subprocess.call("docker buildx prune --force >/dev/null 2>&1", shell=True)
        # Build dist image
        subprocess.call("docker pull nginx:latest", shell=True)
        subprocess.call(f"cd {self._pwd} ; docker buildx build -t meteornext:latest -f build/dist.dockerfile --no-cache --platform linux/amd64 --load .", shell=True)
        subprocess.call(f"docker save meteornext:latest | gzip -9 > {self._pwd}/dist/meteornext.tar.gz", shell=True)

    def __merge_images(self):
        pass
        # subprocess.call("docker manifest create meteornext/meteornext:latest --amend meteornext/meteornext:amd64 --amend meteornext/meteornext:arm64", shell=True)
        # docker manifest push --purge meteornext/meteornext:latest

    def __upload_image(self):
        subprocess.call(f"docker tag meteornext:latest meteornext/meteornext:latest", shell=True)
        subprocess.call(f"docker tag meteornext:latest meteornext/meteornext:{self._version}", shell=True)
        subprocess.call(f"docker login --username meteornext --password-stdin < ~/.docker/auth.txt", shell=True)
        subprocess.call(f"docker push --all-tags meteornext/meteornext", shell=True)

    def __clean(self):
        subprocess.call(f"sudo rm -rf {self._pwd}/.cache", shell=True)
        subprocess.call(f"sudo rm -rf {self._pwd}/dist/client.tar.gz", shell=True)
        subprocess.call(f"sudo rm -rf {self._pwd}/dist/server", shell=True)
        subprocess.call(f"sudo rm -rf {self._pwd}/server/apps/meteor.tar.gz", shell=True)
        subprocess.call(f"sudo rm -rf {self._pwd}/server/apps/monitor.tar.gz", shell=True)
        subprocess.call("docker kill $(docker ps -a -q --filter ancestor=meteornext) >/dev/null 2>&1", shell=True)
        subprocess.call("docker rm $(docker ps -a -q --filter ancestor=meteornext) >/dev/null 2>&1", shell=True)
        subprocess.call("docker rmi meteornext:latest >/dev/null 2>&1", shell=True)
        subprocess.call("docker rmi meteornextbuild:latest >/dev/null 2>&1", shell=True)
        subprocess.call("docker rmi meteornext/meteornext:latest >/dev/null 2>&1", shell=True)
        subprocess.call(f"docker rmi meteornext/meteornext:{self._version} >/dev/null 2>&1", shell=True)
        subprocess.call("docker buildx prune --force >/dev/null 2>&1", shell=True)
