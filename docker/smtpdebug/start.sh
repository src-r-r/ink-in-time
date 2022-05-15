#!/bin/bash
python -m smtpd -c DebuggingServer -n localhost:${SMTP_PORT}
