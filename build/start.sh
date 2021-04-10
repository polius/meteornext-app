#!/bin/bash
cd /root

# Add environment variables
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

# Init 'SECURE' env variable
if [[ -n $SECURE && $SECURE = "True" ]]; then
    export STS='add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload;" always;'
else
    export STS=''
fi
envsubst '${STS}' < /etc/nginx/nginx.conf > /etc/nginx/nginx2.conf
mv /etc/nginx/nginx2.conf /etc/nginx/nginx.conf

# Init app
./server &
nginx
/bin/bash