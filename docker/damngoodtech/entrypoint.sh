#!/bin/ash

# sleep for a bit of time
# in case we're including the smtpdebug server
# TODO: do automatic checks .e.g flag for debug mode

if [ -z $RUN_INIT ]; then
    sleep 2 && python -m gunicorn -w 4 -b 0.0.0.0:5000 src.wsgi:app
fi;