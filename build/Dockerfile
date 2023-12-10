# docker buildx build -t meteornext:latest -f build/Dockerfile --no-cache --platform linux/amd64 --load .
# docker save meteornext:latest | gzip -9 > meteornext.tar.gz
# docker load -i meteornext.tar.gz
# docker buildx prune --force

# Create the container from the nginx image
FROM nginx:latest

# Copy the respective nginx configuration files
COPY build/nginx.conf /etc/nginx/

# Copy the start.sh into docker
COPY build/start.sh /root/

# Copy the backend into docker
COPY server /root/meteornext/

# Copy the frontend into docker
COPY client /tmp/meteornext/client/

# Copy the resources into docker
COPY resources /tmp/meteornext/resources/

# Build project and setup
RUN apt update -qq && \
    apt install unzip -y && \
    apt install procps -y && \
    apt install jq -y && \
    apt install pv -y && \
    apt install default-mysql-client -y && \
    apt install python3 -y && \
    apt install python3-pip -y && \
    apt install npm -y && \
    npm install -g @vue/cli && \
    npm install -g @vue/cli-service && \

    # Install AWS v2
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install -i /usr/bin/aws-cli -b /usr/bin && \
    rm -rf awscliv2.zip aws && \

    # Install Python libs
    python3 -m pip install --no-cache-dir --break-system-packages boto3 && \
    python3 -m pip install --no-cache-dir --break-system-packages requests && \
    python3 -m pip install --no-cache-dir --break-system-packages paramiko && \
    python3 -m pip install --no-cache-dir --break-system-packages sshtunnel && \
    python3 -m pip install --no-cache-dir --break-system-packages pymysql && \
    python3 -m pip install --no-cache-dir --break-system-packages webauthn && \
    python3 -m pip install --no-cache-dir --break-system-packages DBUtils && \
    python3 -m pip install --no-cache-dir --break-system-packages bcrypt && \
    python3 -m pip install --no-cache-dir --break-system-packages pyotp && \
    python3 -m pip install --no-cache-dir --break-system-packages flask && \
    python3 -m pip install --no-cache-dir --break-system-packages flask_cors && \
    python3 -m pip install --no-cache-dir --break-system-packages flask_jwt_extended && \
    python3 -m pip install --no-cache-dir --break-system-packages flask-compress && \
    python3 -m pip install --no-cache-dir --break-system-packages schedule && \
    python3 -m pip install --no-cache-dir --break-system-packages gunicorn[gthread] && \
    python3 -m pip install --no-cache-dir --break-system-packages sentry-sdk[flask] && \
    python3 -m pip install --no-cache-dir --break-system-packages sqlparse && \

    # Install frontend dependencies
    cd /tmp/meteornext/client && \
    npm install && \

    # Copy dependencies into frontend
    cp /tmp/meteornext/resources/one-dark.css /tmp/meteornext/client/node_modules/codemirror/theme/ && \
    cp /tmp/meteornext/resources/mode-mysql.js /tmp/meteornext/client/node_modules/ace-builds/src-noconflict/ && \
    cp /tmp/meteornext/resources/keybinding-vscode.js /tmp/meteornext/client/node_modules/ace-builds/src-noconflict/ && \

    # Build frontend
    export NODE_OPTIONS=--openssl-legacy-provider && \
    npm run build && \

    # Copy frontend into nginx
    mv /tmp/meteornext/client/dist/* /usr/share/nginx/html/ && \
    chown -R root:root /usr/share/nginx/html/ && \
    chmod 755 /root && \
    chmod +x /root/start.sh && \
    find /usr/share/nginx/html -type d -print0 | xargs -0 chmod 755 && \
    find /usr/share/nginx/html -type f -print0 | xargs -0 chmod 644 && \

    # Clean temporary resources
    rm -rf /tmp/* && \
    apt purge python3-pip -y && \
    apt purge npm -y && \
    apt clean -qq

# Start nginx and keep the process from backgrounding and the container from quitting
CMD ["/root/start.sh"]