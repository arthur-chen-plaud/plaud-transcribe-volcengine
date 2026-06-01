#!/bin/bash

set -e

mkdir -p /workspace/logs

if [ "${LOG_TO_FILE:-true}" = "true" ]; then
    echo "log to file enabled"
    cat <<EOF > /etc/supervisor/supervisord.conf
[supervisord]
nodaemon=true
user=root

[program:celery-worker]
command=python /workspace/run_celery.py
directory=/workspace
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stopwaitsecs=600
redirect_stderr=true
stdout_logfile=/workspace/logs/celery-worker.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=5
EOF
else
    echo "log to file disabled"
    cat <<EOF > /etc/supervisor/supervisord.conf
[supervisord]
nodaemon=true
user=root

[program:celery-worker]
command=python /workspace/run_celery.py
directory=/workspace
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stopwaitsecs=600
redirect_stderr=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
EOF
fi

exec supervisord -c /etc/supervisor/supervisord.conf
