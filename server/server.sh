#!/bin/bash
set -m

deployments() {
    while true; do 
        sleep 10;
        python3 server.py --deployments
    done
}
monitoring() {
    while true; do 
        sleep 10;
        python3 server.py --monitoring
    done
}
utils() {
    while true; do 
        sleep 10;
        python3 server.py --utils
    done
}

deployments &
dpid=$!
monitoring &
mpid=$!
utils &
upid=$!
python3 server.py
kill -9 $dpid
kill -9 $mpid
kill -9 $upid