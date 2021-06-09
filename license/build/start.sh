#!/bin/sh
cd /root/licenser

if [[ -n $HOST && -n $USER && -n $PASS && -n $PORT && -n $DB ]]; then
    cat >./licenser.conf <<EOF
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

python3 licenser.py
nginx
/bin/sh