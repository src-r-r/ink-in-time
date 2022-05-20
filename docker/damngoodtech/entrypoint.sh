#!/bin/ash

# sleep for a bit of time
# in case we're including the smtpdebug server
# TODO: do automatic checks .e.g flag for debug mode
sleep 5 && python -m src.wsgi