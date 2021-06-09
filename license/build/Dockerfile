# Create the container from the alpine nginx image
FROM nginx:alpine

# Copy src code
COPY src/ /root/licenser/

# Copy the respective nginx configuration files
COPY build/nginx.conf /etc/nginx/

# Copy the start.sh into docker
COPY build/start.sh /root/licenser/

# Install required software
RUN apk update && \
    apk upgrade && \
    apk add python3 && \
    pip3 install --upgrade pip && \
    pip3 install gunicorn && \
    pip3 install flask && \
    pip3 install flask_cors && \
    pip3 install pymysql && \
    chown root:nginx /root && \
    chmod 750 /root && \
    chmod 764 /root/licenser/start.sh

# Start nginx and keep the process from backgrounding and the container from quitting
CMD ["/root/licenser/start.sh"]