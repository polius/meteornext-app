#!/bin/bash
cd /root

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

# nohup ./server > error.log 2> error.log &
./server &
nginx
/bin/bash