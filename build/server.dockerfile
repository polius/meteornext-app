FROM amazonlinux:1
RUN yum update -y && \
    yum upgrade -y && \
    yum install python36-devel -y && \
    yum install gcc -y && \
    yum install xz -y && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install boto3 && \
    python3 -m pip install requests && \
    python3 -m pip install paramiko && \
    python3 -m pip install sshtunnel && \
    python3 -m pip install pymysql && \
    python3 -m pip install uuid && \
    python3 -m pip install bcrypt && \
    python3 -m pip install flask && \
    python3 -m pip install flask_cors && \
    python3 -m pip install flask_jwt_extended && \
    python3 -m pip install schedule && \
    python3 -m pip install cython && \
    python3 -m pip install gunicorn && \
    python3 -m pip install pyinstaller
WORKDIR /root/build
CMD [ "python3", "build_server.py" ]