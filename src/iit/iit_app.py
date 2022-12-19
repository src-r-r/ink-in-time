import typing as T
from flask import Flask, render_template, request, abort, Request
from datetime import datetime, timedelta
from urllib.parse import parse_qs, parse_qsl
from werkzeug.serving import is_running_from_reloader
import time
import os
import atexit
from calendar import month_name as MN
import pytz
import arrow
from multiprocessing import Process
from pathlib import Path
import logging

from .config import config
from .core import MOCK_ICS_DIR, FLASK_DEBUG, FLASK_ENV
from .checker import check_config
from .db import fetch_more_human_choices
from .calendar import calblock_choices
from .db import compile_choices, get_lastrun_primary
from .email import (
    OrganizerAppointmentRequest as OAR,
    ParticipantAppointmentRequest as PAR,
)

log = logging.getLogger(__name__)
APP_NAME = __name__

TPL_BASE = Path("iit")
IDX_TPL = TPL_BASE / "index"
INC_TPL = TPL_BASE / "inc"
INDEX_TEMPLATE = IDX_TPL / "timeblock_selection.html"
CONFIRM_TEMPLATE = IDX_TPL / "confirmation.html"

CHOICE_TPL_DIR = INC_TPL / "choice"
BLOCK_CHOICE_TPL = CHOICE_TPL_DIR / "appointment_type.html"
YEAR_CHOICE_TPL = CHOICE_TPL_DIR / "year.html"
MONTH_CHOICE_TPL = CHOICE_TPL_DIR / "month.html"
DAY_CHOICE_TPL = CHOICE_TPL_DIR / "day.html"


def template_exists(tpl: Path):
    return (Path("templates") / tpl).exists()


def template_if_exists(tpl: Path):
    if template_exists(tpl):
        return str(tpl)
    return None


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


class IitFlask(Flask):
    def __init__(self, *args, **kwargs):
        super(IitFlask, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):

        # This is a guard against the werkzeig reloader
        if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            run_compile_job()
        return super(IitFlask, self).run(*args, **kwargs)


ICS_MIME = "text/calendar"

app = IitFlask(__name__)

# where the magic happens!



def create_app(
    iit_config=None, config_filename=None, config_obj_path=None, project_name=None
):

    iit_config = iit_config or config

    app.config.url_base = iit_config.url_base
    app.debug = FLASK_DEBUG
    app.env = FLASK_ENV

    engine = create_engine(config["database"]["url"])

    def find_available(block: T.AnyStr, year: int, month: int, day: int):
        ext_field = None
        if block:
            ext_field = "year"
        if year:
            ext_field = "month"
        if month:
            ext_field = "day"
        if day:
            ext_field = None

        stmt = None
        if ext_field:
            stmt = select(distinct(func.extract(ext_field, "from", "timestamp", Block.during)))
        else:
            stmt = select(Block)
        
        if block:
            stmt = stmt.where(Block.name == block)

    # create the application

    # assign the callbacks
    app.after_request(run_compile_job)

    if config_filename:
        app.config.from_pyfile(config_filename)

    @app.route("/", methods=["GET"])
    def get_time_blocks():
        return render_template(template_if_exists(BLOCK_CHOICE_TPL))

    @app.route("/<str:block>", methods=["GET"])
    def get_year(block_name: T.AnyStr):
        return render_template(template_if_exists(YEAR_CHOICE_TPL))

    @app.route("/<str:block>/<int:year>", methods=["GET"])
    def get_month(block_name: T.AnyStr, year: int):
        context = {
            "block": block_name,
            "year": year,
            "month": None,
            "day": None,
        }
        return render_template(template_if_exists(MONTH_CHOICE_TPL), context)

    @app.route("/<str:block>/<int:year>/<int:month>", methods=["GET"])
    def get_day(block_name: T.AnyStr, year: int, month: int):
        context = {
            "block": block_name,
            "year": year,
            "month": month,
            "day": None,
        }
        return render_template(template_if_exists(DAY_CHOICE_TPL), context)

    @app.route("/<str:block>/<int:year>/<int:month>/<int:day>", methods=["GET"])
    def get_day(block_name: T.AnyStr, year: int, month: int, day: int):
        context = {
            "block": block_name,
            "year": year,
            "month": month,
            "day": day,
        }
        return render_template(CONFIRM_TEMPLATE, context)

    return app
