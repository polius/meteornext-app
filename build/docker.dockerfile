# Create the container from the alpine nginx image
FROM nginx:latest

# Copy the web client application into nginx
COPY dist/client.tar.gz /usr/share/nginx/html/

# Copy the server application into docker
COPY dist/server /root/

# Copy the respective nginx configuration files
COPY build/nginx.conf /etc/nginx/

# Copy the start.sh into docker
COPY build/start.sh /root/

# Make all files belong to the nginx user
RUN apt-get update -qq && \
    apt-get install -qq apt-utils > /dev/null 2>&1 && \
    apt-get install -qq procps > /dev/null 2>&1 && \
    apt-get install -qq iputils-ping > /dev/null 2>&1 && \
    tar -zxf /usr/share/nginx/html/client.tar.gz -C /usr/share/nginx/html/ && \
    mv /usr/share/nginx/html/client/* /usr/share/nginx/html/ && \
    rm -rf /usr/share/nginx/html/client* && \
    chown -R root:root /usr/share/nginx/html/ && \
    chmod 755 /root && \
    chmod +x /root/start.sh && \
    find /usr/share/nginx/html -type d -print0 | xargs -0 chmod 755 && \
    find /usr/share/nginx/html -type f -print0 | xargs -0 chmod 644

# Start nginx and keep the process from backgrounding and the container from quitting
CMD ["/root/start.sh"]