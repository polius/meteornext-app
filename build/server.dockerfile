FROM amazonlinux:1
RUN yum update -y && \
    yum install gcc -y && \
    yum install xz -y && \
    yum install python38-devel -y && \
    python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir boto3 && \
    python3 -m pip install --no-cache-dir requests && \
    python3 -m pip install --no-cache-dir paramiko && \
    python3 -m pip install --no-cache-dir sshtunnel && \
    python3 -m pip install --no-cache-dir pymysql && \
    python3 -m pip install --no-cache-dir webauthn && \
    python3 -m pip install --no-cache-dir DBUtils && \
    python3 -m pip install --no-cache-dir bcrypt && \
    python3 -m pip install --no-cache-dir pyotp && \
    python3 -m pip install --no-cache-dir flask && \
    python3 -m pip install --no-cache-dir flask_cors && \
    python3 -m pip install --no-cache-dir flask_jwt_extended && \
    python3 -m pip install --no-cache-dir flask-compress && \
    python3 -m pip install --no-cache-dir schedule && \
    python3 -m pip install --no-cache-dir gunicorn[gthread] && \
    python3 -m pip install --no-cache-dir cython && \
    python3 -m pip install --no-cache-dir pyinstaller && \
    python3 -m pip install --no-cache-dir sentry-sdk[flask] && \
    python3 -m pip install --no-cache-dir sqlparse
WORKDIR /root/build
CMD [ "python3", "build_server.py" ]