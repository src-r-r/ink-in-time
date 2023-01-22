import typing as T
from flask import (
    Flask,
    render_template as flask_render_template,
    request,
    abort,
    Request,
)
from datetime import datetime, timedelta
from urllib.parse import parse_qs, parse_qsl
from werkzeug.serving import is_running_from_reloader
import time
import os
import atexit
from calendar import month_name as MN
import pytz
import celery
import arrow
from multiprocessing import Process
from pathlib import Path
import logging


from celery import Celery
from environ import Env

from flask import Flask
from flask_sqlalchemy import SQLAlchemy as SQLAlchemyExtension

from iit.config import get_config, DB_URL
from iit.tasks.task_loader import get_tasks
from iit.cal.event import OutboundEvent, InboundEvent
from iit.core.const import MOCK_ICS_DIR, FLASK_DEBUG, FLASK_ENV
from iit.controllers.block import find_block_options, find_available
from .email import (
    OrganizerAppointmentRequest as OAR,
    ParticipantAppointmentRequest as PAR,
)
from sqlalchemy import create_engine
from jinja2 import Environment as JinjaEnv, PackageLoader, select_autoescape

env = Env()
Env.read_env(".env")

jinja_env = JinjaEnv(
    loader=PackageLoader("iit", "templates"),
    autoescape=select_autoescape(),
)

config = get_config()

BROKER_URL = env.url("BROKER_URL")

log = logging.getLogger(__name__)
APP_NAME = __name__

TPL_NS = Path("iit")
IDX_TPL = TPL_NS / "index"
INC_TPL = TPL_NS / "inc"
INDEX_TEMPLATE = IDX_TPL / "timeblock_selection.html"
CONFIRM_TEMPLATE = IDX_TPL / "confirmation.html"

CHOICE_TPL_DIR = TPL_NS / "choice"
BLOCK_CHOICE_TPL = CHOICE_TPL_DIR / "block.html"
YEAR_CHOICE_TPL = CHOICE_TPL_DIR / "year.html"
MONTH_CHOICE_TPL = CHOICE_TPL_DIR / "month.html"
DAY_CHOICE_TPL = CHOICE_TPL_DIR / "day.html"
WEEK_CHOICE_TPL = CHOICE_TPL_DIR / "week.html"
TIME_CHOICE_TPL = CHOICE_TPL_DIR / "time.html"


def add_error(context: T.Dict, field: T.AnyStr, code: T.AnyStr):
    errors = context.get("errors", {})
    errors.update(
        {
            field: code,
        }
    )
    context["has_errors"] = True
    context["errors"] = errors
    return context


# callback functions


def extract_tz(req: Request):
    timezones = [{"value": tz, "label": tz} for tz in pytz.all_timezones]
    qs = parse_qs(req.query_string)
    timezone = qs.get(b"timezone", str(config.my_timezone))
    if isinstance(timezone, list):
        timezone = timezone[0].decode("ascii")
    log.debug("timezone = %s", timezone)
    if timezone and (timezone not in pytz.all_timezones):
        log.error("Invalid timezone %s", timezone)
        raise ValueError("Invalid Timezone")
    return (timezone, pytz.timezone(timezone))


ICS_MIME = "text/calendar"

APP_NAME = __name__


def render_template(pth: T.Union[Path, T.AnyStr], *args, **kwargs):
    """Adds a couple of fixes to "render_template" to make it easier."""
    log.debug("Rendering template %s with kwargs=%s", str(pth), kwargs)
    return flask_render_template(str(pth), *args, **kwargs)


# where the magic happens!
def create_app(
    iit_config=None, config_filename=None, config_obj_path=None, project_name=None
):

    iit_config = iit_config or config

    celery_app = Celery("inkintime", broker=BROKER_URL)

    app = Flask(APP_NAME)

    app.config["url_base"] = iit_config["site"]["url_base"]
    app.debug = FLASK_DEBUG
    app.debug = FLASK_ENV.lower() == "debug"

    engine = create_engine(DB_URL)

    if config_filename:
        app.config.from_pyfile(config_filename)

    @app.context_processor
    def add_globals():
        return {
            "config": config,
        }

    @app.route("/", methods=["GET"])
    def get_time_blocks():
        blocks = find_block_options()
        return render_template(
            BLOCK_CHOICE_TPL,
            block_choices=blocks,
        )

    @app.route("/<block>", methods=["GET"])
    def get_year(block: T.AnyStr):
        year_choices = find_available(block=block)
        return render_template(YEAR_CHOICE_TPL, block_choice=block, year_choices=year_choices)

    @app.route("/<block>/<int:year>", methods=["GET"])
    def get_month(block_name: T.AnyStr, year: int):
        context = {
            "block": block_name,
            "year": year,
            "month": None,
            "day": None,
            "choices": find_available(block_name, year, None, None),
        }
        return render_template(template_if_exists(MONTH_CHOICE_TPL), context)

    @app.route("/<block>/<int:year>/<int:month>", methods=["GET"])
    def get_day(block_name: T.AnyStr, year: int, month: int):
        context = {
            "block": block_name,
            "year": year,
            "month": month,
            "day": None,
            "choices": find_available(block_name, year, month, None),
        }
        return render_template(template_if_exists(DAY_CHOICE_TPL), context)

    @app.route("/<block>/<int:year>/<int:month>/<int:day>", methods=["GET", "POST"])
    def pick_a_time(block_name: T.AnyStr, year: int, month: int, day: int):
        context = {
            "block": block_name,
            "year": year,
            "month": month,
            "day": day,
            "choices": find_available(block_name, year, month, day),
        }
        if request.method == "GET":
            return render_template(TIME_CHOICE_TPL, context)
        # if POST...

        for task in get_tasks(config, ["init"]):
            task.apply_async(event=OutboundEvent.from_post_data(start))
        return render_template(template_if_exists(CONFIRM_TEMPLATE))

    return app
