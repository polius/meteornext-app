FROM amazonlinux:1
# RUN yum install gcc -y openssl-devel bzip2-devel libffi-devel zlib-devel wget && \
RUN yum update -y && \
    yum upgrade -y && \
    yum install python36-devel -y && \
    yum install gcc -y && \
    # wget https://www.python.org/ftp/python/3.8.6/Python-3.8.6.tgz && \
    # tar xzf Python-3.8.6.tgz && \
    # cd Python-3.8.6 && \
    # ./configure --enable-optimizations --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib" && \ 
    # make install && \
    yum install xz -y && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install boto3 && \
    python3 -m pip install simplejson && \
    python3 -m pip install requests && \
    python3 -m pip install paramiko && \
    python3 -m pip install sshtunnel && \
    python3 -m pip install pymysql && \
    # python3 -m pip install mysql-connector-python && \
    python3 -m pip install bcrypt && \
    python3 -m pip install pyotp && \
    python3 -m pip install flask && \
    python3 -m pip install flask_cors && \
    python3 -m pip install flask_jwt_extended && \
    python3 -m pip install flask-compress && \
    python3 -m pip install schedule && \
    python3 -m pip install gunicorn && \
    python3 -m pip install gevent && \
    python3 -m pip install gunicorn[gevent] && \
    python3 -m pip install cython && \
    python3 -m pip install pyinstaller
WORKDIR /root/build
CMD [ "python3", "build_server.py" ]