FROM amazonlinux:2
RUN yum update -y && \
    yum install gcc -y && \
    yum install xz -y && \
    amazon-linux-extras enable python3.8 && \
    yum install python38-devel -y && \
    python3.8 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3.8 -m pip install --no-cache-dir boto3 && \
    python3.8 -m pip install --no-cache-dir requests && \
    python3.8 -m pip install --no-cache-dir paramiko && \
    python3.8 -m pip install --no-cache-dir sshtunnel && \
    python3.8 -m pip install --no-cache-dir pymysql && \
    python3.8 -m pip install --no-cache-dir webauthn && \
    python3.8 -m pip install --no-cache-dir DBUtils && \
    python3.8 -m pip install --no-cache-dir bcrypt && \
    python3.8 -m pip install --no-cache-dir pyotp && \
    python3.8 -m pip install --no-cache-dir flask && \
    python3.8 -m pip install --no-cache-dir flask_cors && \
    python3.8 -m pip install --no-cache-dir flask_jwt_extended && \
    python3.8 -m pip install --no-cache-dir flask-compress && \
    python3.8 -m pip install --no-cache-dir schedule && \
    python3.8 -m pip install --no-cache-dir gunicorn[gevent] && \
    python3.8 -m pip install --no-cache-dir cython && \
    python3.8 -m pip install --no-cache-dir pyinstaller
WORKDIR /root/build
CMD [ "python3.8", "build_server.py" ]