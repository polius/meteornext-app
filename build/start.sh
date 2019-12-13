#!/bin/bash
cd /root
nohup ./server >/dev/null 2>&1 &
nginx
/bin/bash