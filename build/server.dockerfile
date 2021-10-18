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
    python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir boto3 && \
    python3 -m pip install --no-cache-dir requests && \
    python3 -m pip install --no-cache-dir simplejson && \
    python3 -m pip install --no-cache-dir paramiko && \
    python3 -m pip install --no-cache-dir sshtunnel && \
    python3 -m pip install --no-cache-dir pymysql && \
    python3 -m pip install --no-cache-dir webauthn==0.4.7 && \
    python3 -m pip install --no-cache-dir DBUtils==2.0.2 && \
    # python3 -m pip install mysql-connector-python && \
    python3 -m pip install --no-cache-dir bcrypt && \
    python3 -m pip install --no-cache-dir pyotp && \
    python3 -m pip install --no-cache-dir flask && \
    python3 -m pip install --no-cache-dir flask_cors && \
    python3 -m pip install --no-cache-dir flask_jwt_extended && \
    python3 -m pip install --no-cache-dir flask-compress && \
    python3 -m pip install --no-cache-dir schedule && \
    python3 -m pip install --no-cache-dir gunicorn && \
    python3 -m pip install --no-cache-dir gevent && \
    python3 -m pip install --no-cache-dir gunicorn[gevent] && \
    python3 -m pip install --no-cache-dir cython && \
    python3 -m pip install --no-cache-dir pyinstaller && \
    python3 -m pip install --no-cache-dir Flask-Limiter
WORKDIR /root/build
CMD [ "python3", "build_server.py" ]