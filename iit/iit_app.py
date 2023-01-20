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
import celery
import arrow
from multiprocessing import Process
from pathlib import Path
import logging

from iit.tasks.task_loader import get_tasks
from iit.cal.event import OutboundEvent, InboundEvent
# from .db import fetch_more_human_choices
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

CHOICE_TPL_DIR = IDX_TPL / "choice"
BLOCK_CHOICE_TPL = CHOICE_TPL_DIR / "appointment_type.html"
YEAR_CHOICE_TPL = CHOICE_TPL_DIR / "year.html"
MONTH_CHOICE_TPL = CHOICE_TPL_DIR / "month.html"
DAY_CHOICE_TPL = CHOICE_TPL_DIR / "day.html"
WEEK_CHOICE_TPL = CHOICE_TPL_DIR / "week.html"
TIME_CHOICE_TPL = CHOICE_TPL_DIR / "time.html"


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


ICS_MIME = "text/calendar"

app = Flask(__name__)

# where the magic happens!

from celery import Celery


def create_app(
    iit_config=None, config_filename=None, config_obj_path=None, project_name=None
):
    from iit.config import config, DB_URL
    from iit.core import MOCK_ICS_DIR, FLASK_DEBUG, FLASK_ENV


    iit_config = iit_config or config

    celery_app = Celery("inkintime", broker=config["broker_url"])

    app.config.url_base = iit_config.url_base
    app.debug = FLASK_DEBUG
    app.env = FLASK_ENV

    engine = create_engine(DB_URL)

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
            stmt = select(
                distinct(func.extract(ext_field, "from", "timestamp", Block.during))
            )
        else:
            stmt = select(Block)

        if block:
            stmt = stmt.where(Block.name == block)

    if config_filename:
        app.config.from_pyfile(config_filename)

    @app.route("/", methods=["GET"])
    def get_time_blocks():
        return render_template(template_if_exists(BLOCK_CHOICE_TPL))

    @app.route("/<str:block>", methods=["GET"])
    def get_year(block_name: T.AnyStr):
        context = {
            "block": block_name,
            "year": None,
            "month": None,
            "day": None,
            "choices": find_available(block_name, None, None, None),
        }
        return render_template(template_if_exists(YEAR_CHOICE_TPL))

    @app.route("/<str:block>/<int:year>", methods=["GET"])
    def get_month(block_name: T.AnyStr, year: int):
        context = {
            "block": block_name,
            "year": year,
            "month": None,
            "day": None,
            "choices": find_available(block_name, year, None, None),
        }
        return render_template(template_if_exists(MONTH_CHOICE_TPL), context)

    @app.route("/<str:block>/<int:year>/<int:month>", methods=["GET"])
    def get_day(block_name: T.AnyStr, year: int, month: int):
        context = {
            "block": block_name,
            "year": year,
            "month": month,
            "day": None,
            "choices": find_available(block_name, year, month, None),
        }
        return render_template(template_if_exists(DAY_CHOICE_TPL), context)

    @app.route("/<str:block>/<int:year>/<int:month>/<int:day>", methods=["GET", "POST"])
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
