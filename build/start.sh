#!/bin/bash
cd /root

if [[ -n $HOST && -n $USER && -n $PASS && -n $PORT && -n $DB ]]; then
    cat >./server.conf <<EOF
{
    "sql": {
        "hostname": "$HOST",
        "username": "$USER",
        "password": "$PASS",
        "port": "$PORT",
        "database": "$DB"
    }
}
EOF
fi

nohup ./server >/dev/null 2>&1 &
nginx
/bin/bash