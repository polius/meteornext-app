# ARG FROM
# FROM ${FROM}
# ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/openssl/lib
FROM amazonlinux:1
RUN echo "Building & Compiling Backend" && \
    # Install binaries
    yum update -y && \
    yum install gcc -y && \
    yum install xz -y && \
    yum install python38-devel -y && \
    # Install Node
    curl -sL https://rpm.nodesource.com/setup_14.x | bash - && \
    yum install nodejs -y && \
    # Install Python dependencies
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
CMD [ "python3", "build_image.py" ]