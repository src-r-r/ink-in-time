from flask import Flask, request, render_template, abort
from datetime import timedelta, datetime
import os
import jinja2
import logging.config
import logging
import pytz
from .core import COMPILEPID_FILE
from .config import config
from .iit_app import create_app

log = logging.getLogger(__name__)


if __name__ == "__main__":
    if COMPILEPID_FILE.exists() and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        msg = """pid file %s exists. This could mean the process didn't stop properly (or it's running after server exited). Please check for PID %s and kill it if desired, or remove the pidfile.
    """
        raise RuntimeError(msg % (COMPILEPID_FILE, COMPILEPID_FILE.read_text()))
    logging.config.dictConfig(config.LOGGING)
    app = create_app()
    app.run(debug=True)
