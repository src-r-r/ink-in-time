from flask import Flask, request, render_template, abort
from datetime import timedelta, datetime
import os
import jinja2
import logging.config
import logging
import pytz
from iit.config import get_config
from iit.iit_app import create_app

log = logging.getLogger(__name__)


if __name__ == "__main__":
    config = get_config()
    logging.config.dictConfig(config["logging"])
    app = create_app()
    app.run(debug=True)
