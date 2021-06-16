#!/bin/bash
cd /root

# Generate 'server.conf' file
if [[ -n $LIC_EMAIL && -n $LIC_KEY && -n $SQL_ENGINE && -n $SQL_HOST && -n $SQL_USER && -n $SQL_PASS && -n $SQL_PORT && -n $SQL_DB ]]; then
    cat >./server.conf <<EOF
{
    "license": {
        "email": "$LIC_EMAIL",
        "key": "$LIC_KEY"
    },
    "sql": {
        "engine": "$SQL_ENGINE",
        "hostname": "$SQL_HOST",
        "username": "$SQL_USER",
        "password": "$SQL_PASS",
        "port": "$SQL_PORT",
        "database": "$SQL_DB"
    }
}
EOF
fi

# Check optional SSL variables
if [[ -n $SQL_SSL_KEY ]]; then
    jq '.sql += {"ssl_client_key": "ssl_key.pem"}' < server.conf > server.tmp && mv server.tmp server.conf
    echo $SQL_SSL_KEY > ./ssl_key.pem
fi
if [[ -n $SQL_SSL_CERT ]]; then
    jq '.sql += {"ssl_client_certificate": "ssl_cert.pem"}' < server.conf > server.tmp && mv server.tmp server.conf
    echo $SQL_SSL_CERT > ./ssl_cert.pem
fi
if [[ -n $SQL_SSL_CA ]]; then
    jq '.sql += {"ssl_ca_certificate": "ssl_ca.pem"}' < server.conf > server.tmp && mv server.tmp server.conf
    echo $SQL_SSL_CA > ./ssl_ca.pem
fi
if [[ -n $SQL_SSL_VERIFY_CA && $SQL_SSL_VERIFY_CA == 1 ]]; then
    jq '.sql += {"ssl_verify_ca": 1}' < server.conf > server.tmp && mv server.tmp server.conf
fi

# Check optional 'SECURE' variable
if [[ -n $SECURE && $SECURE = "1" ]]; then
    export STS='add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload;" always;'
else
    export STS=''
fi
envsubst '${STS}' < /etc/nginx/nginx.conf > /etc/nginx/nginx2.conf
mv /etc/nginx/nginx2.conf /etc/nginx/nginx.conf

# Start Meteor Next
./server &
nginx
/bin/bash