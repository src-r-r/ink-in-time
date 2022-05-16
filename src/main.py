from flask import Flask, request, render_template, abort
from datetime import timedelta, datetime
import jinja2
import logging.config
import logging
import pytz
from .config import config
from .iit_app import create_app

log = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.config.dictConfig(config.LOGGING)
    app = create_app()
    app.run(debug=True)
